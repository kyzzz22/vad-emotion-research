"""Validate browser/device event order and produce trial-level timing QC."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SEMANTIC_SEQUENCE = ["TRIAL_READY", "RATING_START", "RATING_END"]
INDUCED_SEQUENCE = [
    "TRIAL_READY", "BASELINE_START", "BASELINE_END", "STIMULUS_START",
    "STIMULUS_END", "RATING_START", "RATING_END", "RECOVERY_START", "RECOVERY_END",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--allow-incomplete-session", action="store_true")
    return parser.parse_args()


def event_time(group: pd.DataFrame, name: str) -> float | None:
    values = group.loc[group["event_name"] == name, "performance_ms"]
    return float(values.iloc[0]) if len(values) == 1 else None


def validate_trial(group: pd.DataFrame, session_type: str) -> dict[str, object]:
    names = group["event_name"].tolist()
    technical_failure = "TRIAL_TECHNICAL_FAILURE" in names
    expected = SEMANTIC_SEQUENCE if session_type == "semantic" else INDUCED_SEQUENCE
    if technical_failure and session_type == "induced":
        required = ["TRIAL_READY", "BASELINE_START", "BASELINE_END", "TRIAL_TECHNICAL_FAILURE"]
    else:
        required = expected
    missing = [name for name in required if names.count(name) != 1]
    ordered_times = [event_time(group, name) for name in required]
    order_ok = not missing and all(
        earlier <= later for earlier, later in zip(ordered_times, ordered_times[1:])
    )
    baseline_start = event_time(group, "BASELINE_START")
    baseline_end = event_time(group, "BASELINE_END")
    stimulus_start = event_time(group, "STIMULUS_START")
    stimulus_end = event_time(group, "STIMULUS_END")
    rating_start = event_time(group, "RATING_START")
    rating_end = event_time(group, "RATING_END")
    recovery_start = event_time(group, "RECOVERY_START")
    recovery_end = event_time(group, "RECOVERY_END")
    return {
        "participant_id": group["participant_id"].iloc[0],
        "session_id": group["session_id"].iloc[0],
        "session_type": session_type,
        "trial_index": int(group["trial_index"].iloc[0]),
        "concept_id": group["concept_id"].dropna().iloc[0] if group["concept_id"].notna().any() else "",
        "stimulus_id": group["stimulus_id"].dropna().iloc[0] if group["stimulus_id"].notna().any() else "",
        "technical_failure": int(technical_failure),
        "missing_or_duplicate_events": ";".join(missing),
        "order_ok": int(order_ok),
        "baseline_duration_ms": baseline_end - baseline_start if baseline_start is not None and baseline_end is not None else "",
        "stimulus_duration_ms": stimulus_end - stimulus_start if stimulus_start is not None and stimulus_end is not None else "",
        "rating_duration_ms": rating_end - rating_start if rating_start is not None and rating_end is not None else "",
        "recovery_duration_ms": recovery_end - recovery_start if recovery_start is not None and recovery_end is not None else "",
        "marker_errors": int(group["marker_hook_result"].fillna("").str.startswith("error:").sum()),
        "trial_qc": "pass" if order_ok and not missing and not technical_failure else (
            "technical_fail" if technical_failure else "event_fail"
        ),
    }


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.events)
    required = {
        "participant_id", "session_id", "session_type", "event_name",
        "performance_ms", "trial_index", "concept_id", "stimulus_id",
        "marker_hook_result",
    }
    missing_columns = required.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing event columns: {sorted(missing_columns)}")
    if data.empty:
        raise ValueError("Event log is empty")
    data["performance_ms"] = pd.to_numeric(data["performance_ms"], errors="raise")
    if not data["performance_ms"].is_monotonic_increasing:
        raise ValueError("performance_ms is not monotonic")
    participants = data["participant_id"].dropna().unique()
    sessions = data["session_id"].dropna().unique()
    types = data["session_type"].dropna().unique()
    if len(participants) != 1 or len(sessions) != 1 or len(types) != 1:
        raise ValueError("Each event file must contain one participant, session, and session type")
    session_type = str(types[0])
    if session_type not in {"semantic", "induced"}:
        raise ValueError(f"Unknown session type: {session_type}")
    if (data["event_name"] == "SESSION_START").sum() != 1:
        raise ValueError("SESSION_START must occur exactly once")
    ended = (data["event_name"] == "SESSION_END").sum() == 1
    stopped = (data["event_name"] == "PARTICIPANT_STOP").sum() >= 1
    if not args.allow_incomplete_session and not (ended or stopped):
        raise ValueError("Session has neither SESSION_END nor PARTICIPANT_STOP")

    trial_events = data.loc[data["event_name"].isin(set(SEMANTIC_SEQUENCE + INDUCED_SEQUENCE + [
        "TRIAL_TECHNICAL_FAILURE"
    ]))].copy()
    summaries = [
        validate_trial(group.sort_values("performance_ms"), session_type)
        for _, group in trial_events.groupby("trial_index", sort=True)
    ]
    output = pd.DataFrame(summaries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    failures = int((output["trial_qc"] != "pass").sum()) if not output.empty else 0
    print(
        f"PASS session_type={session_type} trials={len(output)} failures={failures} "
        f"output={args.output.name}"
    )


if __name__ == "__main__":
    main()
