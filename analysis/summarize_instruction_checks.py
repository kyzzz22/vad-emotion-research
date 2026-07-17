"""Summarize first-attempt understanding of each condition's rating target."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


CONDITIONS = {"lexical", "prototype", "induced"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.ratings)
    required = {
        "participant_id", "condition", "instruction_check_correct",
        "instruction_check_response",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing instruction-check columns: {sorted(missing)}")

    checks = data[list(required)].drop_duplicates().copy()
    if checks[["instruction_check_correct", "instruction_check_response"]].isna().any().any():
        raise ValueError("Instruction-check fields contain missing values")
    if not checks["condition"].isin(CONDITIONS).all():
        raise ValueError("Unexpected condition in instruction checks")
    if not checks["instruction_check_response"].isin(CONDITIONS).all():
        raise ValueError("Unexpected instruction-check response")
    checks["instruction_check_correct"] = pd.to_numeric(
        checks["instruction_check_correct"], errors="raise"
    ).astype(int)
    if not checks["instruction_check_correct"].isin({0, 1}).all():
        raise ValueError("instruction_check_correct must be 0 or 1")

    duplicate_condition = checks.duplicated(["participant_id", "condition"], keep=False)
    if duplicate_condition.any():
        examples = checks.loc[duplicate_condition, ["participant_id", "condition"]].head()
        raise ValueError(f"Conflicting instruction checks: {examples.to_dict('records')}")

    summary = checks.groupby("condition", as_index=False).agg(
        participants=("participant_id", "nunique"),
        first_attempt_correct_n=("instruction_check_correct", "sum"),
        first_attempt_correct_rate=("instruction_check_correct", "mean"),
    )
    response_counts = (
        checks.groupby(["condition", "instruction_check_response"], as_index=False)
        .size()
        .rename(columns={"size": "participants"})
    )
    args.output.mkdir(parents=True, exist_ok=True)
    checks.sort_values(["participant_id", "condition"]).to_csv(
        args.output / "instruction_checks_participant.csv", index=False
    )
    summary.to_csv(args.output / "instruction_check_summary.csv", index=False)
    response_counts.to_csv(args.output / "instruction_check_response_counts.csv", index=False)
    print(f"PASS checks={len(checks)} participants={checks['participant_id'].nunique()}")


if __name__ == "__main__":
    main()
