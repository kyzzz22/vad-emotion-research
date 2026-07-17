"""First-week CASE pilot for post-stimulus physiological recovery.

The source dataset is read-only. This script reconstructs all 240 emotional
trials, audits joystick behavior during blue screens, and extracts 10-second
HR/SCL recovery bins for a small participant subset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import signal

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "public_data" / "case_pilot" / "case_dataset"
DEFAULT_OUT = ROOT / "public_data" / "case_recovery" / "results"

EMOTION_CATEGORIES = ("amusing", "boring", "relaxed", "scary")
MAIN_CATEGORIES = ("amusing", "scary")
FS = 1000.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--subjects", type=int, nargs="+", default=[1, 2])
    return parser.parse_args()


def load_metadata(case_root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    metadata = case_root / "metadata"
    sequences = pd.read_csv(metadata / "seqs_order.txt", sep="\t")
    durations = pd.read_csv(
        metadata / "videos_duration.txt", sep="\t", usecols=[0, 1], engine="python"
    )
    duration_map = dict(zip(durations["video_name"], durations["video_duration"]))
    return sequences, duration_map


def segment_table(sequence: pd.Series, durations: dict[str, float]) -> pd.DataFrame:
    labels = sequence.astype(str).tolist()
    lengths = np.asarray([durations[label] for label in labels], dtype=float)
    ends = np.cumsum(lengths)
    starts = np.concatenate(([0.0], ends[:-1]))
    table = pd.DataFrame(
        {
            "segment_index": np.arange(len(labels), dtype=int),
            "video_label": labels,
            "start_ms": starts,
            "end_ms": ends,
            "duration_ms": lengths,
        }
    )
    table["category"] = table["video_label"].str.split("-").str[0]
    return table


def build_trial_index(
    sequences: pd.DataFrame, durations: dict[str, float]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subject in range(1, 31):
        segments = segment_table(sequences.iloc[:, subject - 1], durations)
        emotion = segments[segments["category"].isin(EMOTION_CATEGORIES)]
        previous_category: str | None = None
        previous_video_label: str | None = None
        for order, (_, current) in enumerate(emotion.iterrows(), start=1):
            idx = int(current["segment_index"])
            baseline = segments.loc[segments["segment_index"] == idx - 1].iloc[0]
            recovery = segments.loc[segments["segment_index"] == idx + 1].iloc[0]
            category = str(current["category"])
            rows.append(
                {
                    "subject": subject,
                    "trial_order": order,
                    "segment_index": idx,
                    "video_label": current["video_label"],
                    "category": category,
                    "main_condition": category in MAIN_CATEGORIES,
                    "previous_category": previous_category,
                    "previous_video_label": previous_video_label,
                    "stimulus_start_ms": current["start_ms"],
                    "stimulus_end_ms": current["end_ms"],
                    "baseline_segment_index": int(baseline["segment_index"]),
                    "baseline_label": baseline["video_label"],
                    "baseline_start_ms": max(
                        float(baseline["start_ms"]), float(baseline["end_ms"]) - 60_000.0
                    ),
                    "baseline_end_ms": baseline["end_ms"],
                    "recovery_segment_index": int(recovery["segment_index"]),
                    "recovery_label": recovery["video_label"],
                    "recovery_start_ms": recovery["start_ms"],
                    "recovery_end_ms": recovery["end_ms"],
                    "recovery_is_endvid": recovery["video_label"] == "endVid",
                }
            )
            previous_category = category
            previous_video_label = str(current["video_label"])
    trials = pd.DataFrame(rows)
    if len(trials) != 240:
        raise ValueError(f"Expected 240 trials, reconstructed {len(trials)}")
    if not (trials["baseline_label"] == "bluVid").all():
        raise ValueError("Every emotional trial must be preceded by bluVid")
    if not trials["recovery_label"].isin(["bluVid", "endVid"]).all():
        raise ValueError("Unexpected recovery segment label")
    return trials


def assign_segments(time_ms: np.ndarray, segments: pd.DataFrame) -> np.ndarray:
    idx = np.searchsorted(segments["end_ms"].to_numpy(), time_ms, side="left")
    idx[idx >= len(segments)] = -1
    return idx


def scale_annotation(raw: pd.Series) -> pd.Series:
    return 0.5 + 9.0 * (raw + 26_225.0) / 52_450.0


def audit_annotations(
    case_root: Path, sequences: pd.DataFrame, durations: dict[str, float]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subject in range(1, 31):
        segments = segment_table(sequences.iloc[:, subject - 1], durations)
        source = (
            case_root / "data" / "raw" / "annotations" / f"sub{subject}_joystick.txt"
        )
        raw = pd.read_csv(
            source,
            sep="\t",
            header=None,
            names=["time_s", "raw_valence", "raw_arousal"],
            dtype=float,
        )
        raw["segment_index"] = assign_segments(
            (raw["time_s"].to_numpy() * 1000.0), segments
        )
        blue_ids = segments.loc[segments["video_label"] == "bluVid", "segment_index"]
        blue = raw[raw["segment_index"].isin(blue_ids)]
        emotion_ids = segments.loc[
            segments["category"].isin(EMOTION_CATEGORIES), "segment_index"
        ]
        emotional = raw[raw["segment_index"].isin(emotion_ids)]
        rows.append(
            {
                "subject": subject,
                "blue_samples": len(blue),
                "blue_zero_valence_fraction": float((blue["raw_valence"] == 0).mean()),
                "blue_zero_arousal_fraction": float((blue["raw_arousal"] == 0).mean()),
                "emotion_zero_valence_fraction": float(
                    (emotional["raw_valence"] == 0).mean()
                ),
                "emotion_zero_arousal_fraction": float(
                    (emotional["raw_arousal"] == 0).mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def detect_r_peaks(
    ecg: np.ndarray, fs: float = FS
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    finite = np.isfinite(ecg)
    if finite.mean() < 0.99:
        ecg = pd.Series(ecg).interpolate(limit_direction="both").to_numpy()
    sos = signal.butter(3, [5.0, 20.0], btype="bandpass", fs=fs, output="sos")
    filtered = signal.sosfiltfilt(sos, ecg)
    derivative = np.diff(filtered, prepend=filtered[0])
    integrated = np.convolve(
        np.square(derivative), np.ones(int(0.15 * fs)) / int(0.15 * fs), mode="same"
    )
    height = float(np.median(integrated) + 1.5 * np.std(integrated))
    candidates, _ = signal.find_peaks(
        integrated, distance=int(0.30 * fs), height=height
    )
    peaks: list[int] = []
    radius = int(0.10 * fs)
    for candidate in candidates:
        left = max(0, candidate - radius)
        right = min(len(filtered), candidate + radius + 1)
        local = filtered[left:right]
        if not len(local):
            continue
        positive = left + int(np.argmax(local))
        negative = left + int(np.argmin(local))
        peak = positive if abs(filtered[positive]) >= abs(filtered[negative]) else negative
        if not peaks or peak - peaks[-1] >= int(0.30 * fs):
            peaks.append(peak)
        elif abs(filtered[peak]) > abs(filtered[peaks[-1]]):
            peaks[-1] = peak
    peak_array = np.asarray(peaks, dtype=int)
    rr = np.diff(peak_array) / fs
    valid = (rr >= 0.333) & (rr <= 1.5)
    qc = {
        "ecg_finite_fraction": float(finite.mean()),
        "r_peak_count": int(len(peak_array)),
        "rr_valid_fraction": float(valid.mean()) if len(valid) else 0.0,
        "median_hr_bpm": float(np.median(60.0 / rr[valid])) if valid.any() else np.nan,
        "rr_median_s": float(np.median(rr[valid])) if valid.any() else np.nan,
        "rr_p01_s": float(np.quantile(rr[valid], 0.01)) if valid.any() else np.nan,
        "rr_p99_s": float(np.quantile(rr[valid], 0.99)) if valid.any() else np.nan,
    }
    return peak_array, filtered, qc


def load_subject_physiology(case_root: Path, subject: int) -> pd.DataFrame:
    source = (
        case_root / "data" / "raw" / "physiological" / f"sub{subject}_DAQ.txt"
    )
    raw = pd.read_csv(
        source,
        sep="\t",
        header=None,
        usecols=[0, 1, 3],
        names=["time_s", "ecg_v", "gsr_v"],
        dtype=float,
    )
    raw["time_ms"] = raw["time_s"] * 1000.0
    raw["scl_us"] = 24.0 * raw["gsr_v"] - 49.2
    return raw


def load_subject_annotations(case_root: Path, subject: int) -> pd.DataFrame:
    source = (
        case_root / "data" / "raw" / "annotations" / f"sub{subject}_joystick.txt"
    )
    raw = pd.read_csv(
        source,
        sep="\t",
        header=None,
        names=["time_s", "raw_valence", "raw_arousal"],
        dtype=float,
    )
    raw["time_ms"] = raw["time_s"] * 1000.0
    raw["valence"] = scale_annotation(raw["raw_valence"])
    raw["arousal"] = scale_annotation(raw["raw_arousal"])
    return raw


def mean_between(
    values: np.ndarray, times_ms: np.ndarray, start_ms: float, end_ms: float
) -> float:
    mask = (times_ms >= start_ms) & (times_ms < end_ms) & np.isfinite(values)
    return float(np.mean(values[mask])) if mask.any() else np.nan


def count_between(times_ms: np.ndarray, start_ms: float, end_ms: float) -> int:
    return int(((times_ms >= start_ms) & (times_ms < end_ms)).sum())


def make_ecg_qc_plot(
    times_ms: np.ndarray,
    filtered: np.ndarray,
    peaks: np.ndarray,
    subject: int,
    output: Path,
) -> None:
    duration_s = (times_ms[-1] - times_ms[0]) / 1000.0
    centers_s = np.linspace(180.0, max(180.0, duration_s - 180.0), 3)
    fig, axes = plt.subplots(3, 1, figsize=(10, 6.2), sharey=True)
    peak_times_ms = times_ms[peaks]
    for axis, center_s in zip(axes, centers_s):
        start_ms = (center_s - 5.0) * 1000.0
        end_ms = (center_s + 5.0) * 1000.0
        sample_mask = (times_ms >= start_ms) & (times_ms < end_ms)
        peak_mask = (peak_times_ms >= start_ms) & (peak_times_ms < end_ms)
        axis.plot(
            times_ms[sample_mask] / 1000.0,
            filtered[sample_mask],
            color="#325D79",
            linewidth=0.8,
        )
        local_peaks = peaks[peak_mask]
        axis.scatter(
            times_ms[local_peaks] / 1000.0,
            filtered[local_peaks],
            color="#C14953",
            s=18,
            zorder=3,
        )
        axis.set_ylabel("Filtered ECG")
        axis.set_title(f"{center_s - 5.0:.0f}-{center_s + 5.0:.0f} s")
        axis.grid(alpha=0.18)
    axes[-1].set_xlabel("Recording time (s)")
    fig.suptitle(f"Subject {subject}: engineering R-peak check", y=1.01)
    fig.tight_layout()
    fig.savefig(
        output / f"pilot_ecg_qc_sub{subject}.png",
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def extract_subject(
    case_root: Path, subject: int, trials: pd.DataFrame, output: Path
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    physiology = load_subject_physiology(case_root, subject)
    annotations = load_subject_annotations(case_root, subject)
    peaks, filtered_ecg, peak_qc = detect_r_peaks(physiology["ecg_v"].to_numpy())
    peak_times = physiology["time_ms"].to_numpy()[peaks]
    rr_s = np.diff(peak_times) / 1000.0
    hr_times = peak_times[1:]
    valid_rr = (rr_s >= 0.333) & (rr_s <= 1.5)
    hr_values = np.where(valid_rr, 60.0 / rr_s, np.nan)

    p_times = physiology["time_ms"].to_numpy()
    scl = physiology["scl_us"].to_numpy()
    a_times = annotations["time_ms"].to_numpy()
    valence = annotations["valence"].to_numpy()
    arousal = annotations["arousal"].to_numpy()
    make_ecg_qc_plot(p_times, filtered_ecg, peaks, subject, output)

    bin_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    subject_trials = trials[trials["subject"] == subject].copy()
    for _, trial in subject_trials.iterrows():
        baseline_hr = mean_between(
            hr_values,
            hr_times,
            float(trial["baseline_start_ms"]),
            float(trial["baseline_end_ms"]),
        )
        baseline_scl = mean_between(
            scl,
            p_times,
            float(trial["baseline_start_ms"]),
            float(trial["baseline_end_ms"]),
        )
        stimulus_start = float(trial["stimulus_end_ms"]) - 30_000.0
        stimulus_end = float(trial["stimulus_end_ms"])
        stimulus_hr = mean_between(hr_values, hr_times, stimulus_start, stimulus_end)
        stimulus_scl = mean_between(scl, p_times, stimulus_start, stimulus_end)
        stimulus_valence = mean_between(valence, a_times, stimulus_start, stimulus_end)
        stimulus_arousal = mean_between(arousal, a_times, stimulus_start, stimulus_end)

        recovery_deltas_hr: list[float] = []
        recovery_deltas_scl: list[float] = []
        bin_midpoints: list[float] = []
        recovery_start = float(trial["recovery_start_ms"])
        for bin_index in range(12):
            start = recovery_start + bin_index * 10_000.0
            end = start + 10_000.0
            hr = mean_between(hr_values, hr_times, start, end)
            hr_rr_count = count_between(hr_times[np.isfinite(hr_values)], start, end)
            scl_mean = mean_between(scl, p_times, start, end)
            hr_delta = hr - baseline_hr
            scl_delta = scl_mean - baseline_scl
            recovery_deltas_hr.append(hr_delta)
            recovery_deltas_scl.append(scl_delta)
            bin_midpoints.append(bin_index * 10.0 + 5.0)
            bin_rows.append(
                {
                    "subject": subject,
                    "trial_order": trial["trial_order"],
                    "video_label": trial["video_label"],
                    "category": trial["category"],
                    "main_condition": trial["main_condition"],
                    "recovery_is_endvid": trial["recovery_is_endvid"],
                    "recovery_bin": bin_index + 1,
                    "time_mid_s": bin_midpoints[-1],
                    "hr_bpm": hr,
                    "hr_rr_count": hr_rr_count,
                    "hr_delta_bpm": hr_delta,
                    "scl_us": scl_mean,
                    "scl_delta_us": scl_delta,
                    "stimulus_end_valence": stimulus_valence,
                    "stimulus_end_arousal": stimulus_arousal,
                }
            )

        feature: dict[str, object] = {
            "subject": subject,
            "trial_order": trial["trial_order"],
            "video_label": trial["video_label"],
            "category": trial["category"],
            "main_condition": trial["main_condition"],
            "recovery_is_endvid": trial["recovery_is_endvid"],
            "baseline_hr_bpm": baseline_hr,
            "baseline_scl_us": baseline_scl,
            "stimulus_end_hr_bpm": stimulus_hr,
            "stimulus_end_scl_us": stimulus_scl,
            "stimulus_end_valence": stimulus_valence,
            "stimulus_end_arousal": stimulus_arousal,
            "hr_reactivity_bpm": stimulus_hr - baseline_hr,
            "scl_reactivity_us": stimulus_scl - baseline_scl,
            "recovery_hr_min_rr_count": int(
                min(
                    count_between(
                        hr_times[np.isfinite(hr_values)],
                        float(trial["recovery_start_ms"]) + index * 10_000.0,
                        float(trial["recovery_start_ms"]) + (index + 1) * 10_000.0,
                    )
                    for index in range(12)
                )
            ),
        }
        times = np.asarray(bin_midpoints)
        for name, values in (
            ("hr", np.asarray(recovery_deltas_hr, dtype=float)),
            ("scl", np.asarray(recovery_deltas_scl, dtype=float)),
        ):
            finite = np.isfinite(values)
            feature[f"{name}_early_residual"] = float(np.nanmean(values[:3]))
            feature[f"{name}_late_residual"] = float(np.nanmean(values[9:12]))
            feature[f"{name}_recovery_auc_abs"] = float(
                np.trapezoid(np.abs(values[finite]), times[finite])
            )
            feature[f"{name}_recovery_slope_per_s"] = (
                float(np.polyfit(times[finite], values[finite], 1)[0])
                if finite.sum() >= 4
                else np.nan
            )
        feature_rows.append(feature)

    qc: dict[str, object] = {
        "subject": subject,
        "physiology_start_s": float(physiology["time_s"].min()),
        "physiology_end_s": float(physiology["time_s"].max()),
        "annotation_start_s": float(annotations["time_s"].min()),
        "annotation_end_s": float(annotations["time_s"].max()),
        **peak_qc,
    }
    return pd.DataFrame(bin_rows), pd.DataFrame(feature_rows), qc


def make_plot(bins: pd.DataFrame, output: Path) -> None:
    main = bins[bins["category"].isin(MAIN_CATEGORIES)].copy()
    colors = {"amusing": "#218380", "scary": "#B24C63"}
    subjects = sorted(main["subject"].unique())
    fig, axes = plt.subplots(
        len(subjects), 2, figsize=(10, 3.4 * len(subjects)), sharex=True, squeeze=False
    )
    for row, subject in enumerate(subjects):
        current = main[main["subject"] == subject]
        for category in MAIN_CATEGORIES:
            group = current[current["category"] == category]
            for col, variable in enumerate(("hr_delta_bpm", "scl_delta_us")):
                curve = group.groupby("time_mid_s")[variable].mean()
                axes[row, col].plot(
                    curve.index,
                    curve.values,
                    marker="o",
                    color=colors[category],
                    label=category,
                )
        for col, ylabel in enumerate(("HR delta (bpm)", "SCL delta (uS)")):
            axes[row, col].axhline(0, color="#7C838A", linewidth=0.8)
            axes[row, col].set_ylabel(ylabel)
            axes[row, col].set_title(f"Subject {subject}")
            axes[row, col].grid(alpha=0.2)
            axes[row, col].legend(frameon=False)
    for axis in axes[-1]:
        axis.set_xlabel("Seconds after stimulus offset")
    fig.suptitle("CASE first-week recovery engineering check", y=1.01)
    fig.tight_layout()
    fig.savefig(
        output / "pilot_recovery_curves.png",
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sequences, durations = load_metadata(args.case_root)
    trials = build_trial_index(sequences, durations)
    audit = audit_annotations(args.case_root, sequences, durations)

    all_bins = []
    all_features = []
    qc_rows = []
    for subject in args.subjects:
        bins, features, qc = extract_subject(args.case_root, subject, trials, args.output)
        all_bins.append(bins)
        all_features.append(features)
        qc_rows.append(qc)
    bins = pd.concat(all_bins, ignore_index=True)
    features = pd.concat(all_features, ignore_index=True)
    qc = pd.DataFrame(qc_rows)

    trials.to_csv(args.output / "trial_index.csv", index=False)
    audit.to_csv(args.output / "annotation_blue_screen_audit.csv", index=False)
    bins.to_csv(args.output / "pilot_recovery_bins.csv", index=False)
    features.to_csv(args.output / "pilot_trial_features.csv", index=False)
    qc.to_csv(args.output / "pilot_signal_qc.csv", index=False)
    make_plot(bins, args.output)

    manifest = {
        "case_root": str(args.case_root.resolve()),
        "subjects": args.subjects,
        "all_trial_count": int(len(trials)),
        "pilot_trial_count": int(len(features)),
        "pilot_recovery_bin_count": int(len(bins)),
        "blue_zero_valence_fraction_mean": float(
            audit["blue_zero_valence_fraction"].mean()
        ),
        "blue_zero_arousal_fraction_mean": float(
            audit["blue_zero_arousal_fraction"].mean()
        ),
        "main_categories": list(MAIN_CATEGORIES),
        "recovery_bin_seconds": 10,
        "recovery_duration_seconds": 120,
        "ecg_detector_status": "engineering_check_only",
    }
    (args.output / "first_week_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
