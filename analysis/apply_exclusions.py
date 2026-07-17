"""Apply prespecified participant-level exclusions to prepared A2 ratings."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_PATH = ROOT / "materials" / "emotion_concepts.csv"
FAST_THRESHOLD_MS = 800
MAX_FAST_RATE = 0.20


def target_concepts() -> set[str]:
    with CONCEPTS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        return {row["concept_id"] for row in csv.DictReader(handle)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    return parser.parse_args()


def participant_decision(group: pd.DataFrame, concepts: set[str]) -> dict[str, object]:
    participant_id = str(group["participant_id"].iloc[0])
    reasons: list[str] = []
    session_attention = group.groupby("session_id")["attention_check"].min()
    if session_attention.empty or (session_attention < 1).any():
        reasons.append("session_attention_failed")

    usable = group.loc[~group["subjective_qc"].eq("technical_fail")].copy()
    response_times = pd.to_numeric(usable["response_time_ms"], errors="coerce")
    fast_rate = float((response_times < FAST_THRESHOLD_MS).mean()) if len(response_times) else 1.0
    if fast_rate > MAX_FAST_RATE:
        reasons.append("fast_response_rate_above_20pct")

    condition_counts = usable.groupby(["condition", "concept_id"]).size()
    missing_cells = []
    for condition in ("lexical", "prototype", "induced"):
        for concept_id in concepts:
            if condition_counts.get((condition, concept_id), 0) < 1:
                missing_cells.append(f"{condition}:{concept_id}")
    if missing_cells:
        reasons.append("incomplete_primary_cells")

    session_count = int(usable["session_id"].nunique())
    if session_count != 2:
        reasons.append("not_two_sessions")
    return {
        "participant_id": participant_id,
        "included": int(not reasons),
        "exclusion_reasons": ";".join(reasons),
        "fast_response_rate": round(fast_rate, 4),
        "usable_rows": len(usable),
        "technical_fail_rows": int(group["subjective_qc"].eq("technical_fail").sum()),
        "missing_primary_cells": ";".join(missing_cells),
    }


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.ratings)
    required = {
        "participant_id", "session_id", "concept_id", "condition",
        "response_time_ms", "attention_check", "subjective_qc",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing prepared columns: {sorted(missing)}")
    concepts = target_concepts()
    if not set(data["concept_id"]).issubset(concepts):
        raise ValueError("Prepared ratings contain non-target concepts")
    decisions = pd.DataFrame([
        participant_decision(group, concepts)
        for _, group in data.groupby("participant_id", sort=True)
    ])
    included_ids = set(decisions.loc[decisions["included"].eq(1), "participant_id"])
    analysis = data.loc[
        data["participant_id"].isin(included_ids) & data["subjective_qc"].eq("pass")
    ].copy()
    analysis["participant_included"] = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.log.parent.mkdir(parents=True, exist_ok=True)
    analysis.to_csv(args.output, index=False)
    decisions.to_csv(args.log, index=False)
    print(
        f"PASS participants={len(decisions)} included={len(included_ids)} "
        f"excluded={len(decisions) - len(included_ids)} rows={len(analysis)}"
    )


if __name__ == "__main__":
    main()
