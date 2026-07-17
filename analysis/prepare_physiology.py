"""Validate and prepare device-independent trial-level A2 physiology features."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DELTA_TOLERANCE = 0.02


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--physiology", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.physiology)
    required = {
        "participant_id", "concept_id", "stimulus_id", "baseline_start_s",
        "baseline_end_s", "stimulus_start_s", "stimulus_end_s", "recovery_end_s",
        "eda_baseline", "eda_stimulus", "eda_delta", "hr_baseline", "hr_stimulus",
        "hr_delta", "signal_qc_eda", "signal_qc_ecg_ppg",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing physiology columns: {sorted(missing)}")
    if data.duplicated(["participant_id", "concept_id", "stimulus_id"]).any():
        raise ValueError("Duplicate physiology trial keys")
    numeric = [
        "baseline_start_s", "baseline_end_s", "stimulus_start_s", "stimulus_end_s",
        "recovery_end_s", "eda_baseline", "eda_stimulus", "eda_delta",
        "hr_baseline", "hr_stimulus", "hr_delta",
    ]
    data[numeric] = data[numeric].apply(pd.to_numeric, errors="coerce")
    if data[numeric].isna().any().any() or not np.isfinite(data[numeric].to_numpy()).all():
        raise ValueError("Physiology numeric fields contain missing or non-finite values")
    ordered = (
        (data["baseline_start_s"] <= data["baseline_end_s"])
        & (data["baseline_end_s"] <= data["stimulus_start_s"])
        & (data["stimulus_start_s"] < data["stimulus_end_s"])
        & (data["stimulus_end_s"] <= data["recovery_end_s"])
    )
    if not ordered.all():
        raise ValueError("Physiology phase timestamps are not ordered")
    eda_error = (data["eda_delta"] - (data["eda_stimulus"] - data["eda_baseline"])).abs()
    hr_error = (data["hr_delta"] - (data["hr_stimulus"] - data["hr_baseline"])).abs()
    if (eda_error > DELTA_TOLERANCE).any() or (hr_error > DELTA_TOLERANCE).any():
        raise ValueError("Stored delta does not match stimulus minus baseline")
    allowed_qc = {"pass", "partial", "fail"}
    if not data["signal_qc_eda"].isin(allowed_qc).all():
        raise ValueError("Unexpected EDA QC value")
    if not data["signal_qc_ecg_ppg"].isin(allowed_qc).all():
        raise ValueError("Unexpected ECG/PPG QC value")

    data["physiology_qc"] = "pass"
    both_fail = data["signal_qc_eda"].eq("fail") & data["signal_qc_ecg_ppg"].eq("fail")
    any_nonpass = ~data["signal_qc_eda"].eq("pass") | ~data["signal_qc_ecg_ppg"].eq("pass")
    data.loc[any_nonpass, "physiology_qc"] = "partial"
    data.loc[both_fail, "physiology_qc"] = "fail"
    for variable in ("eda_delta", "hr_delta"):
        participant_mean = data.groupby("participant_id")[variable].transform("mean")
        data[f"{variable}_between"] = participant_mean
        data[f"{variable}_within"] = data[variable] - participant_mean
        within_sd = data.loc[data["physiology_qc"].ne("fail"), f"{variable}_within"].std(ddof=1)
        if not np.isfinite(within_sd) or within_sd <= 0:
            raise ValueError(f"Cannot standardize {variable} within-person component")
        data[f"{variable}_within_z"] = data[f"{variable}_within"] / within_sd

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False)
    counts = data["physiology_qc"].value_counts().to_dict()
    print(f"PASS trials={len(data)} qc={counts} output={args.output.name}")


if __name__ == "__main__":
    main()
