"""Prepare an A2 task export without making outcome-dependent exclusions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_PATH = ROOT / "materials" / "emotion_concepts.csv"
FILLERS_PATH = ROOT / "materials" / "semantic_fillers.csv"
TARGET_COLUMN = {
    "JOY": "intensity_joy",
    "AMUSEMENT": "intensity_amusement",
    "TENDERNESS": "intensity_tenderness",
    "ANGER": "intensity_anger",
    "SADNESS": "intensity_sadness",
    "FEAR": "intensity_fear",
}


def ids_from_csv(path: Path) -> set[str]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return {row["concept_id"] for row in csv.DictReader(handle)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.raw)
    required = {
        "participant_id", "concept_id", "condition", "stimulus_id",
        "session_id", "session_order", "block_order", "item_order",
        "valence", "arousal", "dominance", "attention_check",
        *TARGET_COLUMN.values(),
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing raw rating columns: {sorted(missing)}")

    target_ids = ids_from_csv(CONCEPTS_PATH)
    filler_ids = ids_from_csv(FILLERS_PATH)
    unknown = set(data["concept_id"].dropna()) - target_ids - filler_ids
    if unknown:
        raise ValueError(f"Unknown concept IDs: {sorted(unknown)}")
    filler_rows = int(data["concept_id"].isin(filler_ids).sum())
    prepared = data.loc[data["concept_id"].isin(target_ids)].copy()

    if not prepared["condition"].isin({"lexical", "prototype", "induced"}).all():
        raise ValueError("Unexpected condition value")
    technical_failure = prepared.get("notes", pd.Series("", index=prepared.index)).fillna("").str.contains(
        "TRIAL_TECHNICAL_FAILURE", regex=False
    )
    for dimension in ("valence", "arousal", "dominance"):
        prepared[dimension] = pd.to_numeric(prepared[dimension], errors="coerce")
        invalid = prepared[dimension].notna() & ~prepared[dimension].between(1, 9)
        missing_without_failure = prepared[dimension].isna() & ~technical_failure
        if invalid.any() or missing_without_failure.any():
            raise ValueError(f"{dimension} contains invalid or unexplained missing scores")
    induced = prepared["condition"] == "induced"
    if prepared.loc[induced, "stimulus_id"].isna().any() or (prepared.loc[induced, "stimulus_id"] == "").any():
        raise ValueError("Induced rows require stimulus_id")
    if prepared.loc[~induced, "stimulus_id"].fillna("").ne("").any():
        raise ValueError("Semantic rows must not have stimulus_id")

    duplicate_key = prepared.duplicated(
        ["participant_id", "concept_id", "condition", "stimulus_id"], keep=False
    )
    if duplicate_key.any():
        examples = prepared.loc[duplicate_key, [
            "participant_id", "concept_id", "condition", "stimulus_id"
        ]].head().to_dict("records")
        raise ValueError(f"Duplicate rating keys: {examples}")

    prepared["target_emotion_intensity"] = pd.NA
    for concept_id, column in TARGET_COLUMN.items():
        mask = induced & prepared["concept_id"].eq(concept_id)
        values = pd.to_numeric(prepared.loc[mask, column], errors="coerce")
        invalid = values.notna() & ~values.between(1, 9)
        missing_without_failure = values.isna() & ~technical_failure.loc[mask]
        if invalid.any() or missing_without_failure.any():
            raise ValueError(f"{column} contains scores outside 1-9")
        prepared.loc[mask, "target_emotion_intensity"] = values

    prepared["subjective_qc"] = "pass"
    prepared.loc[technical_failure, "subjective_qc"] = "technical_fail"
    attention_failure = pd.to_numeric(prepared["attention_check"], errors="coerce").ne(1)
    prepared.loc[attention_failure & ~technical_failure, "subjective_qc"] = "attention_fail"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(args.output, index=False)
    print(
        f"PASS raw={len(data)} fillers_removed={filler_rows} "
        f"prepared={len(prepared)} output={args.output.name}"
    )


if __name__ == "__main__":
    main()
