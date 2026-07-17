"""Week-two full-sample CASE recovery analysis.

This script validates the engineering ECG detector against HeartPy, processes
all 30 participants, audits ECG/EDA quality, draws recovery curves, fits the
pre-specified simplified mixed models, runs sensitivity analyses, and estimates
cross-condition participant consistency.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import warnings
from pathlib import Path

import heartpy as hp
import matplotlib
import numpy as np
import pandas as pd
import scipy
import statsmodels
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.multitest import multipletests

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import case_recovery_pilot as pilot


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "public_data" / "case_pilot" / "case_dataset"
DEFAULT_OUT = ROOT / "public_data" / "case_recovery" / "week2"
MAIN_CATEGORIES = ("amusing", "scary")
COLORS = {"amusing": "#218380", "scary": "#B24C63"}
FS = 1000.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--stage", choices=("all", "preprocess", "analysis"), default="all"
    )
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260715)
    return parser.parse_args()


def mean_between(
    values: np.ndarray, times_ms: np.ndarray, start_ms: float, end_ms: float
) -> float:
    mask = (times_ms >= start_ms) & (times_ms < end_ms) & np.isfinite(values)
    return float(np.mean(values[mask])) if mask.any() else np.nan


def count_between(times_ms: np.ndarray, start_ms: float, end_ms: float) -> int:
    return int(((times_ms >= start_ms) & (times_ms < end_ms)).sum())


def eda_qc(scl: np.ndarray) -> dict[str, float | int | bool]:
    finite = np.isfinite(scl)
    valid = scl[finite]
    if not len(valid):
        return {
            "scl_finite_fraction": 0.0,
            "scl_min_us": np.nan,
            "scl_max_us": np.nan,
            "scl_negative_fraction": np.nan,
            "scl_over_100_fraction": np.nan,
            "scl_jump_count_gt_1us_per_sample": 0,
            "scl_jump_fraction_gt_1us_per_sample": np.nan,
            "scl_abs_diff_p9999_us": np.nan,
            "scl_start_end_drift_us": np.nan,
            "scl_drift_per_min_us": np.nan,
            "eda_qc_flag": True,
        }
    differences = np.abs(np.diff(valid))
    second_count = len(valid) // 1000
    second_medians = np.median(valid[: second_count * 1000].reshape(-1, 1000), axis=1)
    minutes = np.arange(len(second_medians), dtype=float) / 60.0
    drift_slope = (
        float(np.polyfit(minutes, second_medians, 1)[0])
        if len(second_medians) >= 120
        else np.nan
    )
    edge = min(60_000, len(valid) // 4)
    edge_drift = float(np.median(valid[-edge:]) - np.median(valid[:edge]))
    negative_fraction = float((valid < 0).mean())
    over_100_fraction = float((valid > 100).mean())
    jump_count = int((differences > 1.0).sum())
    jump_fraction = float((differences > 1.0).mean())
    finite_fraction = float(finite.mean())
    flag = bool(
        finite_fraction < 0.99
        or negative_fraction > 0.001
        or over_100_fraction > 0.001
        or jump_fraction > 0.001
        or abs(edge_drift) > 25.0
    )
    return {
        "scl_finite_fraction": finite_fraction,
        "scl_min_us": float(np.min(valid)),
        "scl_max_us": float(np.max(valid)),
        "scl_negative_fraction": negative_fraction,
        "scl_over_100_fraction": over_100_fraction,
        "scl_jump_count_gt_1us_per_sample": jump_count,
        "scl_jump_fraction_gt_1us_per_sample": jump_fraction,
        "scl_abs_diff_p9999_us": float(np.quantile(differences, 0.9999)),
        "scl_start_end_drift_us": edge_drift,
        "scl_drift_per_min_us": drift_slope,
        "eda_qc_flag": flag,
    }


def match_peaks(
    reference: np.ndarray, comparison: np.ndarray, tolerance_samples: int = 100
) -> dict[str, float | int]:
    positions = np.searchsorted(comparison, reference)
    right = comparison[np.clip(positions, 0, len(comparison) - 1)]
    left = comparison[np.clip(positions - 1, 0, len(comparison) - 1)]
    distances = np.minimum(np.abs(reference - right), np.abs(reference - left))
    matched = distances <= tolerance_samples
    matched_count = int(matched.sum())
    return {
        "matched_reference_count": matched_count,
        "reference_match_fraction": float(matched.mean()),
        "comparison_match_fraction": float(matched_count / len(comparison)),
        "matched_median_abs_difference_ms": float(np.median(distances[matched])),
        "matched_p99_abs_difference_ms": float(np.quantile(distances[matched], 0.99)),
    }


def validate_heartpy(case_root: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for subject in (1, 2):
        physiology = pilot.load_subject_physiology(case_root, subject)
        ecg = physiology["ecg_v"].to_numpy()
        custom_peaks, filtered, custom_qc = pilot.detect_r_peaks(ecg)
        polarity = -1 if abs(np.quantile(filtered, 0.001)) > abs(
            np.quantile(filtered, 0.999)
        ) else 1
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            working_data, measures = hp.process(
                polarity * filtered,
                sample_rate=FS,
                bpmmin=40,
                bpmmax=180,
                clean_rr=True,
                clean_rr_method="quotient-filter",
            )
        heartpy_peaks = np.asarray(working_data["peaklist"], dtype=int)
        heartpy_peaks = heartpy_peaks[heartpy_peaks >= 0]
        comparison = match_peaks(custom_peaks, heartpy_peaks)
        rows.append(
            {
                "subject": subject,
                "custom_peak_count": len(custom_peaks),
                "heartpy_peak_count": len(heartpy_peaks),
                "custom_median_hr_bpm": custom_qc["median_hr_bpm"],
                "heartpy_mean_hr_bpm": measures["bpm"],
                "heartpy_polarity": polarity,
                **comparison,
                "validation_pass": bool(
                    comparison["reference_match_fraction"] >= 0.98
                    and comparison["comparison_match_fraction"] >= 0.98
                ),
            }
        )
    return pd.DataFrame(rows)


def extract_subject(
    case_root: Path, subject: int, trials: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    physiology = pilot.load_subject_physiology(case_root, subject)
    annotations = pilot.load_subject_annotations(case_root, subject)
    ecg = physiology["ecg_v"].to_numpy()
    peaks, _, peak_qc = pilot.detect_r_peaks(ecg)
    peak_times = physiology["time_ms"].to_numpy()[peaks]
    rr_s = np.diff(peak_times) / 1000.0
    hr_times = peak_times[1:]
    valid_rr = (rr_s >= 0.333) & (rr_s <= 1.5)
    hr_values = np.where(valid_rr, 60.0 / rr_s, np.nan)
    valid_hr_times = hr_times[np.isfinite(hr_values)]

    p_times = physiology["time_ms"].to_numpy()
    scl = physiology["scl_us"].to_numpy()
    second_count = len(scl) // 1000
    scl_1s = np.nanmedian(scl[: second_count * 1000].reshape(-1, 1000), axis=1)
    scl_times_1s = np.nanmean(
        p_times[: second_count * 1000].reshape(-1, 1000), axis=1
    )
    a_times = annotations["time_ms"].to_numpy()
    valence = annotations["valence"].to_numpy()
    arousal = annotations["arousal"].to_numpy()

    bin_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, object]] = []
    for _, trial in trials[trials["subject"] == subject].iterrows():
        baseline_start = float(trial["baseline_start_ms"])
        baseline_end = float(trial["baseline_end_ms"])
        stimulus_start = float(trial["stimulus_end_ms"]) - 30_000.0
        stimulus_end = float(trial["stimulus_end_ms"])
        recovery_start = float(trial["recovery_start_ms"])

        baseline_hr = mean_between(hr_values, hr_times, baseline_start, baseline_end)
        baseline_scl = mean_between(
            scl_1s, scl_times_1s, baseline_start, baseline_end
        )
        stimulus_hr = mean_between(hr_values, hr_times, stimulus_start, stimulus_end)
        stimulus_scl = mean_between(
            scl_1s, scl_times_1s, stimulus_start, stimulus_end
        )
        stimulus_valence = mean_between(valence, a_times, stimulus_start, stimulus_end)
        stimulus_arousal = mean_between(arousal, a_times, stimulus_start, stimulus_end)

        hr_deltas: list[float] = []
        scl_deltas: list[float] = []
        midpoints: list[float] = []
        rr_counts: list[int] = []
        for index in range(12):
            start = recovery_start + index * 10_000.0
            end = start + 10_000.0
            current_hr = mean_between(hr_values, hr_times, start, end)
            current_scl = mean_between(scl_1s, scl_times_1s, start, end)
            rr_count = count_between(valid_hr_times, start, end)
            hr_delta = current_hr - baseline_hr
            scl_delta = current_scl - baseline_scl
            midpoint = index * 10.0 + 5.0
            hr_deltas.append(hr_delta)
            scl_deltas.append(scl_delta)
            midpoints.append(midpoint)
            rr_counts.append(rr_count)
            bin_rows.append(
                {
                    "subject": subject,
                    "trial_order": int(trial["trial_order"]),
                    "video_label": trial["video_label"],
                    "category": trial["category"],
                    "main_condition": bool(trial["main_condition"]),
                    "previous_category": trial["previous_category"],
                    "previous_video_label": trial["previous_video_label"],
                    "recovery_is_endvid": bool(trial["recovery_is_endvid"]),
                    "recovery_bin": index + 1,
                    "time_mid_s": midpoint,
                    "hr_bpm": current_hr,
                    "hr_rr_count": rr_count,
                    "hr_delta_bpm": hr_delta,
                    "scl_us": current_scl,
                    "scl_delta_us": scl_delta,
                    "stimulus_end_valence": stimulus_valence,
                    "stimulus_end_arousal": stimulus_arousal,
                }
            )

        feature: dict[str, object] = {
            "subject": subject,
            "trial_order": int(trial["trial_order"]),
            "video_label": trial["video_label"],
            "category": trial["category"],
            "main_condition": bool(trial["main_condition"]),
            "previous_category": trial["previous_category"],
            "previous_video_label": trial["previous_video_label"],
            "recovery_is_endvid": bool(trial["recovery_is_endvid"]),
            "baseline_hr_bpm": baseline_hr,
            "baseline_scl_us": baseline_scl,
            "stimulus_end_hr_bpm": stimulus_hr,
            "stimulus_end_scl_us": stimulus_scl,
            "stimulus_end_valence": stimulus_valence,
            "stimulus_end_arousal": stimulus_arousal,
            "hr_reactivity_bpm": stimulus_hr - baseline_hr,
            "scl_reactivity_us": stimulus_scl - baseline_scl,
            "recovery_hr_min_rr_count": min(rr_counts),
            "hr_low_quality": min(rr_counts) < 5,
        }
        times = np.asarray(midpoints)
        for name, values in (
            ("hr", np.asarray(hr_deltas, dtype=float)),
            ("scl", np.asarray(scl_deltas, dtype=float)),
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

    ecg_flag = bool(
        peak_qc["ecg_finite_fraction"] < 0.99
        or peak_qc["rr_valid_fraction"] < 0.95
        or not 40 <= peak_qc["median_hr_bpm"] <= 120
    )
    qc: dict[str, object] = {
        "subject": subject,
        "physiology_start_s": float(physiology["time_s"].min()),
        "physiology_end_s": float(physiology["time_s"].max()),
        "annotation_start_s": float(annotations["time_s"].min()),
        "annotation_end_s": float(annotations["time_s"].max()),
        **peak_qc,
        "ecg_qc_flag": ecg_flag,
        **eda_qc(scl),
    }
    qc["participant_exclusion_flag"] = bool(
        qc["ecg_qc_flag"] or qc["scl_finite_fraction"] < 0.95
    )
    return pd.DataFrame(bin_rows), pd.DataFrame(feature_rows), qc


def preprocess_all(case_root: Path, output: Path) -> None:
    sequences, durations = pilot.load_metadata(case_root)
    trials = pilot.build_trial_index(sequences, durations)
    validation = validate_heartpy(case_root)
    if not validation["validation_pass"].all():
        raise RuntimeError("HeartPy cross-validation did not meet the 98% gate")

    all_bins: list[pd.DataFrame] = []
    all_features: list[pd.DataFrame] = []
    all_qc: list[dict[str, object]] = []
    for subject in range(1, 31):
        print(f"processing subject {subject}/30", flush=True)
        bins, features, qc = extract_subject(case_root, subject, trials)
        all_bins.append(bins)
        all_features.append(features)
        all_qc.append(qc)

    bins = pd.concat(all_bins, ignore_index=True)
    features = pd.concat(all_features, ignore_index=True)
    qc = pd.DataFrame(all_qc)
    trials.to_csv(output / "trial_index.csv", index=False)
    validation.to_csv(output / "ecg_heartpy_validation.csv", index=False)
    bins.to_csv(output / "full_recovery_bins.csv", index=False)
    features.to_csv(output / "full_trial_features.csv", index=False)
    qc.to_csv(output / "participant_signal_qc.csv", index=False)


def bootstrap_curves(
    bins: pd.DataFrame, variable: str, repetitions: int, rng: np.random.Generator
) -> pd.DataFrame:
    participant_curves = (
        bins.groupby(["subject", "category", "time_mid_s"], as_index=False)[variable]
        .mean()
        .sort_values(["subject", "category", "time_mid_s"])
    )
    rows: list[dict[str, object]] = []
    for category in MAIN_CATEGORIES:
        pivot = participant_curves[participant_curves["category"] == category].pivot(
            index="subject", columns="time_mid_s", values=variable
        )
        values = pivot.to_numpy(dtype=float)
        indices = rng.integers(0, len(values), size=(repetitions, len(values)))
        boot = np.nanmean(values[indices, :], axis=1)
        for column, time_mid in enumerate(pivot.columns):
            rows.append(
                {
                    "variable": variable,
                    "category": category,
                    "time_mid_s": float(time_mid),
                    "participant_count": len(values),
                    "mean": float(np.nanmean(values[:, column])),
                    "ci_lower": float(np.nanquantile(boot[:, column], 0.025)),
                    "ci_upper": float(np.nanquantile(boot[:, column], 0.975)),
                    "bootstrap_repetitions": repetitions,
                }
            )
    return pd.DataFrame(rows)


def plot_individual_curves(bins: pd.DataFrame, variable: str, output: Path) -> None:
    participant_curves = bins.groupby(
        ["subject", "category", "time_mid_s"], as_index=False
    )[variable].mean()
    fig, axes = plt.subplots(6, 5, figsize=(15, 17), sharex=True, sharey=True)
    for subject, axis in zip(range(1, 31), axes.flat):
        current = participant_curves[participant_curves["subject"] == subject]
        for category in MAIN_CATEGORIES:
            curve = current[current["category"] == category]
            axis.plot(
                curve["time_mid_s"],
                curve[variable],
                color=COLORS[category],
                linewidth=1.3,
                label=category,
            )
        axis.axhline(0, color="#7C838A", linewidth=0.7)
        axis.set_title(f"P{subject}", fontsize=9)
        axis.grid(alpha=0.15)
    axes[0, 0].legend(frameon=False, fontsize=8)
    fig.supxlabel("Seconds after stimulus offset")
    fig.supylabel(variable)
    fig.suptitle(f"Participant recovery curves: {variable}", y=0.995)
    fig.tight_layout()
    fig.savefig(
        output / f"individual_{variable}_curves.png",
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def plot_overall_curves(summary: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
    for axis, variable, ylabel in zip(
        axes, ("hr_delta_bpm", "scl_delta_us"), ("HR delta (bpm)", "SCL delta (uS)")
    ):
        current = summary[summary["variable"] == variable]
        for category in MAIN_CATEGORIES:
            curve = current[current["category"] == category].sort_values("time_mid_s")
            x = curve["time_mid_s"].to_numpy()
            axis.plot(x, curve["mean"], color=COLORS[category], label=category)
            axis.fill_between(
                x,
                curve["ci_lower"].to_numpy(),
                curve["ci_upper"].to_numpy(),
                color=COLORS[category],
                alpha=0.18,
            )
        axis.axhline(0, color="#7C838A", linewidth=0.8)
        axis.set_xlabel("Seconds after stimulus offset")
        axis.set_ylabel(ylabel)
        axis.grid(alpha=0.18)
        axis.legend(frameon=False)
    fig.suptitle("CASE recovery trajectories with participant-bootstrap 95% CI")
    fig.tight_layout()
    fig.savefig(
        output / "overall_recovery_curves_ci.png",
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def prepare_model_data(bins: pd.DataFrame) -> pd.DataFrame:
    data = bins[bins["category"].isin(MAIN_CATEGORIES)].copy()
    data["condition_scary"] = (data["category"] == "scary").astype(int)
    data["time_linear"] = (data["time_mid_s"] - 60.0) / 60.0
    data["time_quadratic"] = data["time_linear"] ** 2
    data["arousal_z"] = (
        data["stimulus_end_arousal"] - data["stimulus_end_arousal"].mean()
    ) / data["stimulus_end_arousal"].std(ddof=0)
    data["order_z"] = (data["trial_order"] - data["trial_order"].mean()) / data[
        "trial_order"
    ].std(ddof=0)
    data["recovery_is_endvid"] = data["recovery_is_endvid"].astype(int)
    data["previous_category_filled"] = data["previous_category"].fillna("none")
    for variable in ("hr_delta_bpm", "scl_delta_us"):
        data[f"{variable}_within_z"] = data.groupby("subject")[variable].transform(
            lambda values: (values - values.mean()) / values.std(ddof=0)
        )
    return data


def fit_one_model(
    data: pd.DataFrame, outcome: str, variant: str
) -> tuple[pd.DataFrame, dict[str, object]]:
    base_terms = (
        "condition_scary * time_linear + condition_scary * time_quadratic "
        "+ arousal_z + order_z"
    )
    current = data.copy()
    model_outcome = outcome
    if variant == "primary":
        formula = f"{outcome} ~ {base_terms} + recovery_is_endvid"
    elif variant == "exclude_endvid":
        current = current[current["recovery_is_endvid"] == 0].copy()
        formula = f"{outcome} ~ {base_terms}"
    elif variant == "previous_condition":
        formula = (
            f"{outcome} ~ {base_terms} + recovery_is_endvid "
            "+ C(previous_category_filled)"
        )
    elif variant == "within_subject_z":
        model_outcome = f"{outcome}_within_z"
        formula = f"{model_outcome} ~ {base_terms} + recovery_is_endvid"
    elif variant == "exclude_eda_review":
        current = current[~current["eda_qc_flag"]].copy()
        formula = f"{outcome} ~ {base_terms} + recovery_is_endvid"
    else:
        raise ValueError(variant)

    required = [model_outcome, "arousal_z", "order_z", "subject"]
    current = current.dropna(subset=required)
    if variant == "within_subject_z":
        model = smf.gee(
            formula,
            groups="subject",
            data=current,
            family=sm.families.Gaussian(),
            cov_struct=sm.cov_struct.Exchangeable(),
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = model.fit(maxiter=200)
        intervals = result.conf_int()
        coefficient_rows = []
        for term, estimate in result.params.items():
            coefficient_rows.append(
                {
                    "outcome": outcome,
                    "model_outcome": model_outcome,
                    "variant": variant,
                    "model_type": "GEE_exchangeable",
                    "term": term,
                    "estimate": float(estimate),
                    "std_error": float(result.bse[term]),
                    "z_value": float(estimate / result.bse[term]),
                    "p_value": float(result.pvalues[term]),
                    "ci_lower": float(intervals.loc[term, 0]),
                    "ci_upper": float(intervals.loc[term, 1]),
                }
            )
        fit = {
            "outcome": outcome,
            "variant": variant,
            "model_type": "GEE_exchangeable",
            "formula": formula,
            "n_observations": int(len(current)),
            "n_participants": int(current["subject"].nunique()),
            "converged": bool(result.converged),
            "optimizer": "GEE_IRLS",
            "log_likelihood": np.nan,
            "aic": np.nan,
            "bic": np.nan,
            "random_intercept_variance": np.nan,
            "random_time_slope_variance": np.nan,
            "random_intercept_time_covariance": np.nan,
            "residual_variance": float(result.scale),
            "warning_count": len(caught),
            "warnings": " | ".join(dict.fromkeys(str(item.message) for item in caught)),
        }
        return pd.DataFrame(coefficient_rows), fit

    model = smf.mixedlm(
        formula, current, groups=current["subject"], re_formula="1 + time_linear"
    )
    result = None
    optimizer = ""
    messages: list[str] = []
    for method in ("lbfgs", "powell"):
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                candidate = model.fit(reml=False, method=method, maxiter=500, disp=False)
            messages.extend(str(item.message) for item in caught)
            result = candidate
            optimizer = method
            if candidate.converged:
                break
        except Exception as error:  # recorded for reproducibility
            messages.append(f"{method}: {type(error).__name__}: {error}")
    if result is None:
        raise RuntimeError(f"Mixed model failed: {outcome}/{variant}: {messages}")

    intervals = result.conf_int()
    coefficient_rows: list[dict[str, object]] = []
    for term, estimate in result.fe_params.items():
        coefficient_rows.append(
            {
                "outcome": outcome,
                "model_outcome": model_outcome,
                "variant": variant,
                "model_type": "MixedLM_random_intercept_time",
                "term": term,
                "estimate": float(estimate),
                "std_error": float(result.bse_fe[term]),
                "z_value": float(estimate / result.bse_fe[term]),
                "p_value": float(result.pvalues[term]),
                "ci_lower": float(intervals.loc[term, 0]),
                "ci_upper": float(intervals.loc[term, 1]),
            }
        )
    fit = {
        "outcome": outcome,
        "variant": variant,
        "model_type": "MixedLM_random_intercept_time",
        "formula": formula,
        "n_observations": int(result.nobs),
        "n_participants": int(current["subject"].nunique()),
        "converged": bool(result.converged),
        "optimizer": optimizer,
        "log_likelihood": float(result.llf),
        "aic": float(result.aic),
        "bic": float(result.bic),
        "random_intercept_variance": float(result.cov_re.iloc[0, 0]),
        "random_time_slope_variance": float(result.cov_re.iloc[1, 1]),
        "random_intercept_time_covariance": float(result.cov_re.iloc[0, 1]),
        "residual_variance": float(result.scale),
        "warning_count": len(messages),
        "warnings": " | ".join(dict.fromkeys(messages)),
    }
    return pd.DataFrame(coefficient_rows), fit


def fit_models(data: pd.DataFrame, output: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    coefficients: list[pd.DataFrame] = []
    fits: list[dict[str, object]] = []
    for outcome in ("hr_delta_bpm", "scl_delta_us"):
        variants = [
            "primary",
            "exclude_endvid",
            "previous_condition",
            "within_subject_z",
        ]
        if outcome == "scl_delta_us":
            variants.append("exclude_eda_review")
        for variant in variants:
            current_coefficients, current_fit = fit_one_model(data, outcome, variant)
            coefficients.append(current_coefficients)
            fits.append(current_fit)
    coefficient_table = pd.concat(coefficients, ignore_index=True)
    fit_table = pd.DataFrame(fits)
    coefficient_table.to_csv(output / "mixed_model_coefficients.csv", index=False)
    fit_table.to_csv(output / "mixed_model_fit.csv", index=False)
    key_terms = coefficient_table[
        coefficient_table["term"].isin(
            [
                "condition_scary",
                "time_linear",
                "time_quadratic",
                "condition_scary:time_linear",
                "condition_scary:time_quadratic",
                "arousal_z",
            ]
        )
    ]
    key_terms.to_csv(output / "sensitivity_key_terms.csv", index=False)
    return coefficient_table, fit_table


def bootstrap_spearman(
    x: np.ndarray, y: np.ndarray, repetitions: int, rng: np.random.Generator
) -> tuple[float, float]:
    estimates = np.full(repetitions, np.nan)
    for index in range(repetitions):
        sample = rng.integers(0, len(x), size=len(x))
        if np.unique(x[sample]).size > 1 and np.unique(y[sample]).size > 1:
            estimates[index] = stats.spearmanr(x[sample], y[sample]).statistic
    return float(np.nanquantile(estimates, 0.025)), float(
        np.nanquantile(estimates, 0.975)
    )


def analyze_consistency(
    features: pd.DataFrame,
    output: Path,
    repetitions: int,
    rng: np.random.Generator,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics = [
        "hr_recovery_auc_abs",
        "hr_late_residual",
        "hr_recovery_slope_per_s",
        "scl_recovery_auc_abs",
        "scl_late_residual",
        "scl_recovery_slope_per_s",
    ]
    participant = (
        features[features["category"].isin(MAIN_CATEGORIES)]
        .groupby(["subject", "category"], as_index=False)[metrics]
        .mean()
    )
    participant.to_csv(output / "participant_condition_features.csv", index=False)
    rows: list[dict[str, object]] = []
    for metric in metrics:
        pivot = participant.pivot(index="subject", columns="category", values=metric)
        x = pivot["amusing"].to_numpy(dtype=float)
        y = pivot["scary"].to_numpy(dtype=float)
        finite = np.isfinite(x) & np.isfinite(y)
        result = stats.spearmanr(x[finite], y[finite])
        lower, upper = bootstrap_spearman(
            x[finite], y[finite], repetitions, rng
        )
        rows.append(
            {
                "metric": metric,
                "participant_count": int(finite.sum()),
                "spearman_rho": float(result.statistic),
                "p_value": float(result.pvalue),
                "ci_lower": lower,
                "ci_upper": upper,
                "bootstrap_repetitions": repetitions,
            }
        )
    results = pd.DataFrame(rows)
    rejected, adjusted, _, _ = multipletests(
        results["p_value"].to_numpy(), alpha=0.05, method="fdr_bh"
    )
    results["q_value_bh"] = adjusted
    results["fdr_reject_05"] = rejected
    results.to_csv(output / "cross_condition_consistency.csv", index=False)
    return participant, results


def plot_consistency(participant: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for axis, metric, label in zip(
        axes,
        ("hr_recovery_auc_abs", "scl_recovery_auc_abs"),
        ("HR absolute recovery AUC", "SCL absolute recovery AUC"),
    ):
        pivot = participant.pivot(index="subject", columns="category", values=metric)
        axis.scatter(pivot["amusing"], pivot["scary"], color="#325D79", alpha=0.8)
        for subject, row in pivot.iterrows():
            axis.annotate(str(subject), (row["amusing"], row["scary"]), fontsize=6)
        axis.set_xlabel("Amusing")
        axis.set_ylabel("Scary")
        axis.set_title(label)
        axis.grid(alpha=0.18)
    fig.suptitle("Cross-condition participant ranking")
    fig.tight_layout()
    fig.savefig(
        output / "cross_condition_auc_scatter.png",
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)


def analysis_stage(output: Path, repetitions: int, seed: int) -> None:
    bins = pd.read_csv(output / "full_recovery_bins.csv")
    features = pd.read_csv(output / "full_trial_features.csv")
    qc = pd.read_csv(output / "participant_signal_qc.csv")
    excluded = set(qc.loc[qc["participant_exclusion_flag"], "subject"])
    if excluded:
        bins = bins[~bins["subject"].isin(excluded)].copy()
        features = features[~features["subject"].isin(excluded)].copy()

    main_bins = bins[bins["category"].isin(MAIN_CATEGORIES)].copy()
    main_bins = main_bins.merge(
        qc[["subject", "eda_qc_flag"]], on="subject", how="left", validate="many_to_one"
    )
    rng = np.random.default_rng(seed)
    curve_tables = [
        bootstrap_curves(main_bins, variable, repetitions, rng)
        for variable in ("hr_delta_bpm", "scl_delta_us")
    ]
    curve_summary = pd.concat(curve_tables, ignore_index=True)
    curve_summary.to_csv(output / "overall_curve_bootstrap_ci.csv", index=False)
    plot_individual_curves(main_bins, "hr_delta_bpm", output)
    plot_individual_curves(main_bins, "scl_delta_us", output)
    plot_overall_curves(curve_summary, output)

    model_data = prepare_model_data(main_bins)
    model_data.to_csv(output / "model_input_bins.csv", index=False)
    fit_models(model_data, output)
    participant, _ = analyze_consistency(features, output, repetitions, rng)
    plot_consistency(participant, output)


def write_manifest(
    args: argparse.Namespace, elapsed_s: float, output: Path
) -> None:
    bins = pd.read_csv(output / "full_recovery_bins.csv")
    features = pd.read_csv(output / "full_trial_features.csv")
    qc = pd.read_csv(output / "participant_signal_qc.csv")
    validation = pd.read_csv(output / "ecg_heartpy_validation.csv")
    fits = pd.read_csv(output / "mixed_model_fit.csv")
    consistency = pd.read_csv(output / "cross_condition_consistency.csv")
    manifest = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "case_root": str(args.case_root.resolve()),
        "participant_count": int(qc["subject"].nunique()),
        "participant_exclusion_count": int(qc["participant_exclusion_flag"].sum()),
        "trial_count": int(len(features)),
        "main_trial_count": int(features["category"].isin(MAIN_CATEGORIES).sum()),
        "recovery_bin_count": int(len(bins)),
        "main_recovery_bin_count": int(
            bins["category"].isin(MAIN_CATEGORIES).sum()
        ),
        "heartpy_validation_all_pass": bool(validation["validation_pass"].all()),
        "models_all_converged": bool(fits["converged"].all()),
        "consistency_metric_count": int(len(consistency)),
        "bootstrap_repetitions": args.bootstrap,
        "scl_window_estimator": "mean of 1-second medians",
        "seed": args.seed,
        "elapsed_seconds": round(elapsed_s, 3),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
            "heartpy": hp.__version__,
        },
        "neurokit2_note": (
            "0.2.13 installed but unusable because Windows application control "
            "blocked a downloaded scikit-learn DLL; HeartPy used instead."
        ),
    }
    (output / "week2_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=True), flush=True)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if args.stage in ("all", "preprocess"):
        preprocess_all(args.case_root, args.output)
    if args.stage in ("all", "analysis"):
        analysis_stage(args.output, args.bootstrap, args.seed)
    if args.stage == "all":
        write_manifest(args, time.time() - started, args.output)


if __name__ == "__main__":
    main()
