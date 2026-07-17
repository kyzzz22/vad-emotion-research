"""Summarize pilot induction quality using prespecified A2 decision rules."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TARGET_COLUMN = {
    "JOY": "intensity_joy",
    "AMUSEMENT": "intensity_amusement",
    "TENDERNESS": "intensity_tenderness",
    "ANGER": "intensity_anger",
    "SADNESS": "intensity_sadness",
    "FEAR": "intensity_fear",
}
INTENSITY_COLUMNS = [*TARGET_COLUMN.values(), "intensity_disgust"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def validate(data: pd.DataFrame) -> pd.DataFrame:
    required = {
        "participant_id", "concept_id", "condition", "stimulus_id",
        "valence", "arousal", "dominance", "familiarity", "discomfort",
        *INTENSITY_COLUMNS,
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing pilot columns: {sorted(missing)}")
    induced = data.loc[data["condition"] == "induced"].copy()
    if induced.empty:
        raise ValueError("No induced rows found")
    if not induced["concept_id"].isin(TARGET_COLUMN).all():
        raise ValueError("Unexpected concept_id in induced rows")
    numeric = ["valence", "arousal", "dominance", "familiarity", "discomfort", *INTENSITY_COLUMNS]
    induced[numeric] = induced[numeric].apply(pd.to_numeric, errors="raise")
    if not induced[numeric].apply(lambda column: column.between(1, 9).all()).all():
        raise ValueError("Pilot ratings must be within 1-9")
    return induced


def add_trial_metrics(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in data.iterrows():
        target_column = TARGET_COLUMN[row["concept_id"]]
        non_target_columns = [column for column in INTENSITY_COLUMNS if column != target_column]
        non_target_values = row[non_target_columns].astype(float)
        target = float(row[target_column])
        all_values = row[INTENSITY_COLUMNS].astype(float)
        rank = 1 + int((all_values > target).sum())
        rows.append({
            **row.to_dict(),
            "target_score": target,
            "max_non_target_score": float(non_target_values.max()),
            "target_minus_max_non_target": target - float(non_target_values.max()),
            "target_rank": rank,
            "hit": int(target >= 5 and target >= float(non_target_values.max())),
            "tied_highest": int(target == float(all_values.max()) and (all_values == target).sum() > 1),
        })
    return pd.DataFrame(rows)


def summarize(data: pd.DataFrame) -> pd.DataFrame:
    summary = data.groupby(["concept_id", "stimulus_id"], as_index=False).agg(
        n=("participant_id", "nunique"),
        target_mean=("target_score", "mean"),
        max_non_target_mean=("max_non_target_score", "mean"),
        target_difference_mean=("target_minus_max_non_target", "mean"),
        target_rank_mean=("target_rank", "mean"),
        hit_rate=("hit", "mean"),
        tied_highest_rate=("tied_highest", "mean"),
        valence_mean=("valence", "mean"),
        arousal_mean=("arousal", "mean"),
        dominance_mean=("dominance", "mean"),
        familiarity_mean=("familiarity", "mean"),
        discomfort_mean=("discomfort", "mean"),
    )
    summary["hard_fail_target_below_4_5"] = summary["target_mean"] < 4.5
    summary["hard_fail_rank_below_top2"] = summary["target_rank_mean"] > 2
    summary["hard_fail_discomfort_8plus"] = summary["discomfort_mean"] >= 8
    fail_columns = [column for column in summary if column.startswith("hard_fail_")]
    summary["hard_fail_any"] = summary[fail_columns].any(axis=1)
    summary["selection_score"] = (
        summary["target_difference_mean"] + summary["hit_rate"]
        - 0.05 * summary["familiarity_mean"]
    )
    summary["within_concept_priority"] = summary.groupby("concept_id")["selection_score"].rank(
        method="first", ascending=False
    ).astype(int)
    numeric_columns = summary.select_dtypes(include=[np.number]).columns
    summary[numeric_columns] = summary[numeric_columns].round(4)
    return summary.sort_values(["concept_id", "within_concept_priority"])


def main() -> None:
    args = parse_args()
    data = validate(pd.read_csv(args.ratings))
    trial_metrics = add_trial_metrics(data)
    summary = summarize(trial_metrics)
    args.output.mkdir(parents=True, exist_ok=True)
    trial_metrics.to_csv(args.output / "pilot_trial_metrics.csv", index=False)
    summary.to_csv(args.output / "pilot_stimulus_summary.csv", index=False)
    print(f"PASS trials={len(trial_metrics)} stimuli={len(summary)} output={args.output.name}")


if __name__ == "__main__":
    main()
