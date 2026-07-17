"""Generate prespecified A2 tables and publication figures from analysis ratings."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from run_analysis import DIMENSIONS, build_distances, validate_ratings


PALETTE = {"lexical": "#3267a8", "prototype": "#c47b20", "induced": "#24815b"}
LABEL_OFFSETS = {
    "FEAR": (5, 10),
    "ANGER": (5, -10),
    "SADNESS": (5, 8),
    "JOY": (5, 8),
    "AMUSEMENT": (5, -9),
    "TENDERNESS": (5, 8),
}
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
    parser.add_argument("--seed", type=int, default=20260714)
    return parser.parse_args()


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator, iterations: int = 5000) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return np.nan, np.nan
    means = np.mean(rng.choice(values, size=(iterations, len(values)), replace=True), axis=1)
    return tuple(np.quantile(means, [0.025, 0.975]))


def save_centroids(data: pd.DataFrame, output: Path) -> None:
    centroids = data.groupby(["concept_id", "condition"], as_index=False)[DIMENSIONS].mean()
    centroids.to_csv(output / "concept_condition_centroids.csv", index=False)
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    for concept_id, concept in centroids.groupby("concept_id"):
        ordered = concept.set_index("condition").reindex(["lexical", "prototype", "induced"]).dropna()
        ax.plot(ordered["valence"], ordered["arousal"], color="#aab2ae", linewidth=1, zorder=1)
        for condition, row in ordered.iterrows():
            ax.scatter(row["valence"], row["arousal"], s=58, color=PALETTE[condition], zorder=2)
        if "induced" in ordered.index:
            row = ordered.loc["induced"]
            ax.annotate(
                concept_id.title(), (row["valence"], row["arousal"]),
                xytext=LABEL_OFFSETS.get(concept_id, (5, 4)), textcoords="offset points", fontsize=8,
            )
    handles = [plt.Line2D([0], [0], marker="o", linestyle="", color=color, label=label.title()) for label, color in PALETTE.items()]
    ax.legend(handles=handles, frameon=False, loc="best")
    ax.set(xlabel="Valence (1-9)", ylabel="Arousal (1-9)", xlim=(1, 9), ylim=(1, 9))
    ax.axvline(5, color="#d6dcda", linewidth=0.8)
    ax.axhline(5, color="#d6dcda", linewidth=0.8)
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(output / "figure1_va_centroids.png", dpi=300)
    plt.close(fig)


def save_distance_pairing(data: pd.DataFrame, output: Path) -> None:
    distances = build_distances(data)
    participant = distances.groupby(["participant_id", "source"], as_index=False)["distance"].mean()
    participant.to_csv(output / "participant_mean_distances.csv", index=False)
    wide = participant.pivot(index="participant_id", columns="source", values="distance").dropna()
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    x = {"lexical": 0, "prototype": 1}
    for _, row in wide.iterrows():
        ax.plot([0, 1], [row["lexical"], row["prototype"]], color="#b7bfbb", alpha=0.55, linewidth=0.8)
    for source in ("lexical", "prototype"):
        values = wide[source].to_numpy()
        mean = values.mean()
        ci = bootstrap_ci(values, np.random.default_rng(110 + x[source]))
        ax.scatter(x[source], mean, s=90, color=PALETTE[source], zorder=3)
        ax.vlines(x[source], ci[0], ci[1], color=PALETTE[source], linewidth=3, zorder=2)
    ax.set_xticks([0, 1], ["Lexical-induced", "Prototype-induced"])
    ax.set_ylabel("Standardized VAD distance")
    ax.set_xlim(-0.35, 1.35)
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(output / "figure2_paired_distances.png", dpi=300)
    plt.close(fig)


def dimension_differences(data: pd.DataFrame) -> pd.DataFrame:
    aggregated = data.groupby(["participant_id", "concept_id", "condition"], as_index=False)[DIMENSIONS].mean()
    wide = aggregated.pivot(index=["participant_id", "concept_id"], columns="condition", values=DIMENSIONS)
    rows = []
    for source in ("lexical", "prototype"):
        for dimension in DIMENSIONS:
            values = wide[(dimension, "induced")] - wide[(dimension, source)]
            for (participant_id, concept_id), value in values.items():
                rows.append({
                    "participant_id": participant_id,
                    "concept_id": concept_id,
                    "source": source,
                    "dimension": dimension,
                    "induced_minus_source": value,
                })
    return pd.DataFrame(rows)


def save_dimension_differences(data: pd.DataFrame, output: Path, seed: int) -> None:
    differences = dimension_differences(data)
    differences.to_csv(output / "dimension_differences_long.csv", index=False)
    participant = differences.groupby(["participant_id", "source", "dimension"], as_index=False)["induced_minus_source"].mean()
    rng = np.random.default_rng(seed)
    summaries = []
    for (source, dimension), group in participant.groupby(["source", "dimension"]):
        values = group["induced_minus_source"].to_numpy()
        low, high = bootstrap_ci(values, rng)
        summaries.append({
            "source": source,
            "dimension": dimension,
            "mean": values.mean(),
            "ci_low": low,
            "ci_high": high,
            "n": len(values),
        })
    summary = pd.DataFrame(summaries)
    summary.to_csv(output / "dimension_difference_summary.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    offsets = {"lexical": -0.12, "prototype": 0.12}
    dimensions = ["valence", "arousal", "dominance"]
    for source in ("lexical", "prototype"):
        subset = summary.set_index(["source", "dimension"]).loc[source]
        xs = np.arange(len(dimensions)) + offsets[source]
        means = subset.loc[dimensions, "mean"].to_numpy()
        lows = subset.loc[dimensions, "ci_low"].to_numpy()
        highs = subset.loc[dimensions, "ci_high"].to_numpy()
        ax.errorbar(xs, means, yerr=[means - lows, highs - means], fmt="o", capsize=4, color=PALETTE[source], label=source.title())
    ax.axhline(0, color="#7d8782", linewidth=1)
    ax.set_xticks(np.arange(3), ["Valence", "Arousal", "Dominance"])
    ax.set_ylabel("Induced minus source rating")
    ax.legend(frameon=False)
    sns.despine(ax=ax)
    fig.tight_layout()
    fig.savefig(output / "figure3_dimension_differences.png", dpi=300)
    plt.close(fig)


def save_manipulation_summary(data: pd.DataFrame, output: Path) -> None:
    induced = data.loc[data["condition"].eq("induced")].copy()
    if induced.empty or not set(INTENSITY_COLUMNS).issubset(induced.columns):
        return
    rows = []
    for _, row in induced.iterrows():
        target_column = TARGET_COLUMN[row["concept_id"]]
        target = float(row[target_column])
        non_target = max(float(row[column]) for column in INTENSITY_COLUMNS if column != target_column)
        rows.append({
            "participant_id": row["participant_id"],
            "concept_id": row["concept_id"],
            "stimulus_id": row["stimulus_id"],
            "target_score": target,
            "max_non_target_score": non_target,
            "target_minus_max_non_target": target - non_target,
            "hit": int(target >= 5 and target >= non_target),
        })
    trials = pd.DataFrame(rows)
    summary = trials.groupby(["concept_id", "stimulus_id"], as_index=False).agg(
        n=("participant_id", "nunique"),
        target_mean=("target_score", "mean"),
        max_non_target_mean=("max_non_target_score", "mean"),
        target_difference_mean=("target_minus_max_non_target", "mean"),
        hit_rate=("hit", "mean"),
    )
    summary.to_csv(output / "stimulus_manipulation_summary.csv", index=False)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.ratings)
    if "subjective_qc" in data.columns:
        data = data.loc[data["subjective_qc"].eq("pass")].copy()
    validate_ratings(data)
    sns.set_theme(style="white", context="paper", font_scale=1.1)
    save_centroids(data, args.output)
    save_distance_pairing(data, args.output)
    save_dimension_differences(data, args.output, args.seed)
    save_manipulation_summary(data, args.output)
    print(f"PASS participants={data['participant_id'].nunique()} output={args.output.name}")


if __name__ == "__main__":
    main()
