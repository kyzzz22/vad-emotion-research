"""Robust category-level analyses for the DREAMER x NRC-VAD comparison.

This stage intentionally starts from the frozen, trial-level alignment table.
It does not redistribute or require the licensed DREAMER signal file.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT
    / "public_data"
    / "dreamer_pilot"
    / "results"
    / "dreamer_trial_alignment_all_sensitivities.csv"
)
DEFAULT_OUTPUT = ROOT / "results" / "dreamer_nrc_robustness"
DIMS = ("valence", "arousal", "dominance")
DIM_LABELS = {"valence": "Valence", "arousal": "Arousal", "dominance": "Dominance"}
DIM_LABELS_JA = {
    "valence": "快―不快（Valence）",
    "arousal": "覚醒度（Arousal）",
    "dominance": "支配性（Dominance）",
}
EMOTION_LABELS_JA = {
    "happiness": "幸福",
    "excitement": "興奮",
    "anger": "怒り",
    "calmness": "平静",
    "amusement": "愉快",
    "fear": "恐怖",
    "surprise": "驚き",
    "disgust": "嫌悪",
    "sadness": "悲しみ",
}
COLORS = {"valence": "#000000", "arousal": "#000000", "dominance": "#000000"}
MARKERS = {"valence": "o", "arousal": "s", "dominance": "^"}
LABEL_OFFSETS = {
    "valence": {
        "calmness": (-4, 14), "excitement": (6, -18), "happiness": (6, 10),
        "amusement": (6, -10), "surprise": (6, -14),
    },
    "arousal": {
        "calmness": (4, 5), "sadness": (4, 5), "excitement": (-30, 9),
        "happiness": (-48, -16), "fear": (8, 14), "disgust": (10, -17),
        "surprise": (18, -16), "amusement": (-34, -24), "anger": (8, -25),
    },
    "dominance": {
        "sadness": (-42, 8), "disgust": (8, 14), "fear": (8, -18),
        "calmness": (8, 8), "anger": (8, 14), "excitement": (8, -18),
        "amusement": (8, -28), "happiness": (8, 8), "surprise": (8, 8),
    },
}
SEED = 20260718


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap", type=int, default=5000)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def holm_adjust(values: pd.Series) -> pd.Series:
    p = values.to_numpy(dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p) - rank) * p[index])
        adjusted[index] = min(running, 1.0)
    return pd.Series(adjusted, index=values.index)


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x - x.mean()
    y = y - y.mean()
    denominator = np.linalg.norm(x) * np.linalg.norm(y)
    return float(np.dot(x, y) / denominator) if denominator else np.nan


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    return pearson(stats.rankdata(x), stats.rankdata(y))


def exact_correlation_p(
    x: np.ndarray, y: np.ndarray, permutations: np.ndarray
) -> tuple[float, float]:
    """Two-sided exact label-permutation p value for Pearson correlation."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    y = np.asarray(y, dtype=float) - np.mean(y)
    denominator = np.linalg.norm(x) * np.linalg.norm(y)
    observed = float(np.dot(x, y) / denominator)
    null = np.empty(len(permutations), dtype=float)
    batch_size = 25_000
    for start in range(0, len(permutations), batch_size):
        stop = min(start + batch_size, len(permutations))
        null[start:stop] = y[permutations[start:stop]] @ x / denominator
    return observed, float(np.mean(np.abs(null) >= abs(observed) - 1e-12))


def standardized_congruence(x: np.ndarray, y: np.ndarray) -> float:
    """Axis-preserving congruence after standardizing each VAD dimension."""
    zx = stats.zscore(np.asarray(x, dtype=float), axis=0, ddof=1)
    zy = stats.zscore(np.asarray(y, dtype=float), axis=0, ddof=1)
    return float(np.sum(zx * zy) / np.sqrt(np.sum(zx**2) * np.sum(zy**2)))


def category_table(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("emotion", as_index=False)
        .agg(
            **{f"{dim}_elicited": (f"{dim}_elicited", "mean") for dim in DIMS},
            **{f"{dim}_nrc": (f"{dim}_nrc", "first") for dim in DIMS},
        )
        .sort_values("emotion")
        .reset_index(drop=True)
    )


def exact_tests(data: pd.DataFrame, permutations: np.ndarray) -> pd.DataFrame:
    rows = []
    for (term_set, orientation), frame in data.groupby(
        ["term_set", "dominance_orientation"], sort=True
    ):
        categories = category_table(frame)
        for dim in DIMS:
            x = categories[f"{dim}_nrc"].to_numpy()
            y = categories[f"{dim}_elicited"].to_numpy()
            r, pearson_p = exact_correlation_p(x, y, permutations)
            rho, spearman_p = exact_correlation_p(
                stats.rankdata(x), stats.rankdata(y), permutations
            )
            rows.append(
                {
                    "term_set": term_set,
                    "dominance_orientation": orientation,
                    "dimension": dim,
                    "n_emotions": len(categories),
                    "pearson_r": r,
                    "pearson_exact_p": pearson_p,
                    "spearman_rho": rho,
                    "spearman_exact_p": spearman_p,
                }
            )
    result = pd.DataFrame(rows)
    for method in ("pearson", "spearman"):
        result[f"{method}_holm_p"] = result.groupby(
            ["term_set", "dominance_orientation"]
        )[f"{method}_exact_p"].transform(holm_adjust)
    return result


def global_configuration_test(
    categories: pd.DataFrame, permutations: np.ndarray
) -> dict[str, float | int]:
    x = categories[[f"{dim}_nrc" for dim in DIMS]].to_numpy()
    y = categories[[f"{dim}_elicited" for dim in DIMS]].to_numpy()
    zx = stats.zscore(x, axis=0, ddof=1)
    zy = stats.zscore(y, axis=0, ddof=1)
    denominator = np.sqrt(np.sum(zx**2) * np.sum(zy**2))
    observed = float(np.sum(zx * zy) / denominator)
    null = np.empty(len(permutations), dtype=float)
    batch_size = 25_000
    for start in range(0, len(permutations), batch_size):
        stop = min(start + batch_size, len(permutations))
        null[start:stop] = np.einsum(
            "bij,ij->b", zy[permutations[start:stop]], zx
        ) / denominator
    return {
        "n_emotions": len(categories),
        "configuration_congruence": observed,
        "exact_p_greater": float(np.mean(null >= observed - 1e-12)),
        "null_mean": float(null.mean()),
        "null_sd": float(null.std(ddof=1)),
    }


def influence_analysis(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (term_set, orientation), frame in data.groupby(
        ["term_set", "dominance_orientation"], sort=True
    ):
        categories = category_table(frame)
        for omitted in categories["emotion"]:
            keep = categories["emotion"] != omitted
            for dim in DIMS:
                x = categories.loc[keep, f"{dim}_nrc"].to_numpy()
                y = categories.loc[keep, f"{dim}_elicited"].to_numpy()
                rows.append(
                    {
                        "term_set": term_set,
                        "dominance_orientation": orientation,
                        "omitted_emotion": omitted,
                        "dimension": dim,
                        "pearson_r": pearson(x, y),
                        "spearman_rho": spearman(x, y),
                    }
                )
    return pd.DataFrame(rows)


def affine_parameters(categories: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in DIMS:
        x = categories[f"{dim}_nrc"].to_numpy()
        y = categories[f"{dim}_elicited"].to_numpy()
        slope, intercept = np.polyfit(x, y, 1)
        rows.append(
            {
                "dimension": dim,
                "slope": slope,
                "intercept": intercept,
                "r_squared": pearson(x, y) ** 2,
            }
        )
    return pd.DataFrame(rows)


def loeo_residuals(categories: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for held_out in range(len(categories)):
        keep = np.arange(len(categories)) != held_out
        row: dict[str, float | str] = {"emotion": categories.loc[held_out, "emotion"]}
        for dim in DIMS:
            x = categories[f"{dim}_nrc"].to_numpy()
            y = categories[f"{dim}_elicited"].to_numpy()
            slope, intercept = np.polyfit(x[keep], y[keep], 1)
            row[f"residual_{dim}"] = y[held_out] - (intercept + slope * x[held_out])
        row["calibrated_residual_va"] = float(
            np.hypot(row["residual_valence"], row["residual_arousal"])
        )
        row["calibrated_residual_vad"] = float(
            np.sqrt(sum(float(row[f"residual_{dim}"]) ** 2 for dim in DIMS))
        )
        rows.append(row)
    return pd.DataFrame(rows)


def hierarchical_bootstrap(
    main: pd.DataFrame, n_bootstrap: int, rng: np.random.Generator
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    participants = np.sort(main["participant"].unique())
    films = np.sort(main["film_id"].unique())
    emotions = np.sort(main["emotion"].unique())
    participant_index = {value: index for index, value in enumerate(participants)}
    film_index = {value: index for index, value in enumerate(films)}
    values = np.full((len(participants), len(films), len(DIMS)), np.nan)
    for row in main.itertuples(index=False):
        p = participant_index[row.participant]
        f = film_index[row.film_id]
        for d, dim in enumerate(DIMS):
            values[p, f, d] = getattr(row, f"{dim}_elicited")
    if np.isnan(values).any():
        raise ValueError("The main trial table is not a complete participant x film design")

    emotion_films = {
        emotion: np.array(
            [film_index[value] for value in main.loc[main["emotion"] == emotion, "film_id"].unique()]
        )
        for emotion in emotions
    }
    categories = category_table(main).set_index("emotion").loc[emotions].reset_index()
    nrc = categories[[f"{dim}_nrc" for dim in DIMS]].to_numpy()

    corr_draws = np.empty((n_bootstrap, len(DIMS)))
    slope_draws = np.empty((n_bootstrap, len(DIMS)))
    congruence_draws = np.empty(n_bootstrap)
    residual_draws = np.empty((n_bootstrap, len(emotions), 2))

    for draw in range(n_bootstrap):
        sampled_participants = rng.integers(0, len(participants), len(participants))
        elicited = np.empty((len(emotions), len(DIMS)))
        for e, emotion in enumerate(emotions):
            available = emotion_films[emotion]
            sampled_films = rng.choice(available, size=len(available), replace=True)
            elicited[e] = values[np.ix_(sampled_participants, sampled_films)].mean(axis=(0, 1))
        boot_categories = categories[["emotion"]].copy()
        for d, dim in enumerate(DIMS):
            boot_categories[f"{dim}_nrc"] = nrc[:, d]
            boot_categories[f"{dim}_elicited"] = elicited[:, d]
            corr_draws[draw, d] = pearson(nrc[:, d], elicited[:, d])
            slope_draws[draw, d] = np.polyfit(nrc[:, d], elicited[:, d], 1)[0]
        congruence_draws[draw] = standardized_congruence(nrc, elicited)
        residual = loeo_residuals(boot_categories).set_index("emotion").loc[emotions]
        residual_draws[draw, :, 0] = residual["calibrated_residual_va"]
        residual_draws[draw, :, 1] = residual["calibrated_residual_vad"]

    correlation_rows = []
    slope_rows = []
    for d, dim in enumerate(DIMS):
        correlation_rows.append(
            {
                "dimension": dim,
                "bootstrap_ci_low": np.quantile(corr_draws[:, d], 0.025),
                "bootstrap_ci_high": np.quantile(corr_draws[:, d], 0.975),
            }
        )
        slope_rows.append(
            {
                "dimension": dim,
                "slope_ci_low": np.quantile(slope_draws[:, d], 0.025),
                "slope_ci_high": np.quantile(slope_draws[:, d], 0.975),
            }
        )
    correlation_rows.append(
        {
            "dimension": "global_configuration",
            "bootstrap_ci_low": np.quantile(congruence_draws, 0.025),
            "bootstrap_ci_high": np.quantile(congruence_draws, 0.975),
        }
    )

    residual_rows = []
    for e, emotion in enumerate(emotions):
        residual_rows.append(
            {
                "emotion": emotion,
                "residual_va_ci_low": np.quantile(residual_draws[:, e, 0], 0.025),
                "residual_va_ci_high": np.quantile(residual_draws[:, e, 0], 0.975),
                "residual_vad_ci_low": np.quantile(residual_draws[:, e, 1], 0.025),
                "residual_vad_ci_high": np.quantile(residual_draws[:, e, 1], 0.975),
            }
        )
    return pd.DataFrame(correlation_rows), pd.DataFrame(slope_rows), pd.DataFrame(residual_rows)


def save_figure(fig: plt.Figure, output: Path, stem: str) -> None:
    fig.savefig(output / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    svg_path = output / f"{stem}.svg"
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    svg = "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
    svg_path.write_text(f"{svg}\n", encoding="utf-8")
    plt.close(fig)


def make_figures(
    categories: pd.DataFrame,
    exact: pd.DataFrame,
    influence: pd.DataFrame,
    affine: pd.DataFrame,
    residual: pd.DataFrame,
    output: Path,
) -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Meiryo",
                "Yu Gothic",
                "Hiragino Sans",
                "Noto Sans JP",
                "DejaVu Sans",
            ],
            "font.weight": "normal",
            "font.size": 10.5,
            "text.color": "#000000",
            "axes.labelcolor": "#000000",
            "axes.titlecolor": "#000000",
            "axes.titlesize": 12.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 10.5,
            "xtick.color": "#000000",
            "ytick.color": "#000000",
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": True,
            "axes.spines.bottom": True,
            "axes.edgecolor": "#000000",
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "figure.dpi": 120,
            "legend.fontsize": 9.5,
            "svg.fonttype": "none",
        }
    )

    main_exact = exact[
        (exact["term_set"] == "noun")
        & (exact["dominance_orientation"] == "reported")
    ].set_index("dimension")
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.2), sharex=True, sharey=True)
    for ax, dim in zip(axes, DIMS):
        x = categories[f"{dim}_nrc"].to_numpy()
        y = categories[f"{dim}_elicited"].to_numpy()
        ax.axline((-1, -1), (1, 1), color="#B8B8B8", linewidth=1, linestyle="--")
        slope, intercept = np.polyfit(x, y, 1)
        grid = np.linspace(-1, 1, 100)
        ax.plot(grid, intercept + slope * grid, color="#000000", linewidth=2)
        ax.scatter(
            x,
            y,
            color="#000000",
            marker=MARKERS[dim],
            edgecolor="white",
            linewidth=0.7,
            s=62,
            zorder=3,
        )
        for _, row in categories.iterrows():
            offset = LABEL_OFFSETS.get(dim, {}).get(row["emotion"], (4, 4))
            ax.annotate(
                EMOTION_LABELS_JA[row["emotion"]],
                (row[f"{dim}_nrc"], row[f"{dim}_elicited"]),
                xytext=offset,
                textcoords="offset points",
                fontsize=8.5,
                color="#000000",
            )
        test = main_exact.loc[dim]
        ax.set_title(
            f"{DIM_LABELS_JA[dim]}\n"
            f"r = {test['pearson_r']:.2f}、正確 p = {test['pearson_exact_p']:.3f}"
        )
        ax.set_xlabel("NRC語彙規範値")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_aspect("equal", adjustable="box")
    axes[0].set_ylabel("DREAMER誘発評定平均")
    fig.suptitle(
        "次元別のクロスコンテクスト整合性",
        y=1.02,
        fontsize=14,
        fontweight="bold",
        color="#000000",
    )
    fig.tight_layout()
    save_figure(fig, output, "figure_1_dimension_alignment")

    slopes = affine
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    y = np.arange(len(slopes))
    for index, row in slopes.iterrows():
        color = COLORS[row["dimension"]]
        ax.errorbar(
            row["slope"],
            index,
            xerr=[[row["slope"] - row["slope_ci_low"]], [row["slope_ci_high"] - row["slope"]]],
            fmt="o",
            color="#000000",
            ecolor="#000000",
            capsize=4,
            markersize=7,
        )
    ax.axvline(1, color="#666666", linestyle="--", linewidth=1, label="同一尺度（傾き = 1）")
    ax.axvline(0, color="#C8C8C8", linewidth=1)
    ax.set_yticks(y, [DIM_LABELS_JA[value] for value in slopes["dimension"]])
    ax.set_xlabel("NRCからDREAMERへの回帰係数（階層ブートストラップ95% CI）")
    ax.set_title("クロスコンテクストの尺度圧縮")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    save_figure(fig, output, "figure_2_scale_compression")

    main_influence = influence[
        (influence["term_set"] == "noun")
        & (influence["dominance_orientation"] == "reported")
    ]
    emotions = sorted(main_influence["omitted_emotion"].unique())
    fig, ax = plt.subplots(figsize=(9.3, 4.7))
    x = np.arange(len(emotions))
    offsets = np.linspace(-0.22, 0.22, len(DIMS))
    for offset, dim in zip(offsets, DIMS):
        frame = main_influence[main_influence["dimension"] == dim].set_index("omitted_emotion").loc[emotions]
        ax.scatter(
            x + offset,
            frame["pearson_r"],
            label=DIM_LABELS_JA[dim],
            color="#000000",
            marker=MARKERS[dim],
            s=45,
        )
    ax.axhline(0, color="#A8A8A8", linewidth=1)
    ax.set_xticks(x, [EMOTION_LABELS_JA[value] for value in emotions], rotation=25, ha="right")
    ax.set_ylabel("1感情除外後の Pearson r")
    ax.set_title("1感情除外による影響分析")
    ax.legend(frameon=False, ncol=3)
    fig.tight_layout()
    save_figure(fig, output, "figure_3_influence_diagnostics")

    ordered = residual.sort_values("calibrated_residual_vad")
    fig, ax = plt.subplots(figsize=(8.2, 5.1))
    y = np.arange(len(ordered))
    xerr = np.vstack(
        [
            ordered["calibrated_residual_vad"] - ordered["residual_vad_ci_low"],
            ordered["residual_vad_ci_high"] - ordered["calibrated_residual_vad"],
        ]
    )
    ax.errorbar(
        ordered["calibrated_residual_vad"],
        y,
        xerr=xerr,
        fmt="o",
        color="#000000",
        ecolor="#000000",
        capsize=3,
        markersize=7,
    )
    ax.set_yticks(y, [EMOTION_LABELS_JA[value] for value in ordered["emotion"]])
    ax.set_xlabel("LOEO校正VAD残差（階層ブートストラップ95% CI）")
    ax.set_title("アフィン校正後の感情別乖離")
    fig.tight_layout()
    save_figure(fig, output, "figure_4_calibrated_discrepancy")


def write_summary(
    exact: pd.DataFrame,
    global_test: dict[str, float | int],
    correlation_ci: pd.DataFrame,
    affine: pd.DataFrame,
    influence: pd.DataFrame,
    residual: pd.DataFrame,
    output: Path,
) -> None:
    main = exact[
        (exact["term_set"] == "noun")
        & (exact["dominance_orientation"] == "reported")
    ].merge(correlation_ci, on="dimension")
    influence_main = influence[
        (influence["term_set"] == "noun")
        & (influence["dominance_orientation"] == "reported")
    ]
    lines = [
        "# DREAMER x NRC-VAD 稳健性分析报告",
        "",
        "## 推断单位与分析定位",
        "",
        "核心跨数据库检验的推断单位是9个情绪类别，而不是414个试次。参与者和影片双层bootstrap用于量化DREAMER质心的不确定性，但仅有每类两段影片，因此刺激总体的不确定性仍会被低估。",
        "",
        "## 精确类别置换检验",
        "",
        "| 维度 | Pearson r | exact p | Holm p | hierarchical bootstrap 95% CI | Spearman rho | exact p | Holm p |",
        "|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for _, row in main.iterrows():
        lines.append(
            f"| {DIM_LABELS[row['dimension']]} | {row['pearson_r']:.3f} | "
            f"{row['pearson_exact_p']:.4f} | {row['pearson_holm_p']:.4f} | "
            f"[{row['bootstrap_ci_low']:.3f}, {row['bootstrap_ci_high']:.3f}] | "
            f"{row['spearman_rho']:.3f} | {row['spearman_exact_p']:.4f} | "
            f"{row['spearman_holm_p']:.4f} |"
        )
    global_ci = correlation_ci.set_index("dimension").loc["global_configuration"]
    lines.extend(
        [
            "",
            "## 整体三维构型",
            "",
            f"保持V/A/D轴含义不旋转、分别标准化后，整体构型一致性为 "
            f"`C={global_test['configuration_congruence']:.3f}`，单侧精确置换 "
            f"`p={global_test['exact_p_greater']:.4f}`，双层bootstrap 95% CI "
            f"`[{global_ci['bootstrap_ci_low']:.3f}, {global_ci['bootstrap_ci_high']:.3f}]`。",
            "",
            "该指标表示三条对应轴上的平均结构相似性，不允许通过旋转把Valence解释成Arousal，因而比无约束Procrustes更符合本研究的构念问题。",
            "",
            "## 全局量尺映射",
            "",
            "| 维度 | NRC到DREAMER斜率 | 截距 | R2 |",
            "|---|---:|---:|---:|",
        ]
    )
    for _, row in affine.iterrows():
        lines.append(
            f"| {DIM_LABELS[row['dimension']]} | {row['slope']:.3f} | "
            f"{row['intercept']:.3f} | {row['r_squared']:.3f} |"
        )
    lines.extend(
        [
            "",
            "斜率低于1表示DREAMER类别均值相对NRC词汇常模更集中，但不能单独区分量表差异、刺激强度和跨样本差异。",
            "",
            "## 情绪特异校准残差",
            "",
            "| 情绪 | LOEO VAD残差 | hierarchical bootstrap 95% CI |",
            "|---|---:|---|",
        ]
    )
    for _, row in residual.sort_values("calibrated_residual_vad").iterrows():
        lines.append(
            f"| {row['emotion']} | {row['calibrated_residual_vad']:.3f} | "
            f"[{row['residual_vad_ci_low']:.3f}, {row['residual_vad_ci_high']:.3f}] |"
        )
    lines.extend(["", "## 逐类影响范围", ""])
    for dim in DIMS:
        values = influence_main.loc[influence_main["dimension"] == dim, "pearson_r"]
        lines.append(
            f"- {DIM_LABELS[dim]}：删除任一情绪后的 Pearson r 范围为 "
            f"`[{values.min():.3f}, {values.max():.3f}]`。"
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- 显著相关支持类别结构的跨情境对应，不证明绝对坐标等价或测量不变性。",
            "- 校准残差是后验探索性排序；区间较宽时不能宣称某一情绪确定地比另一情绪更不一致。",
            "- Dominance方向反转只改变相关符号，不改善证据强度。其心理解释需结合DREAMER原始SAM呈现方向与题干。",
            "- 当前研究是跨样本二手数据比较，无法把差异归因于词义理解或影片诱发本身。",
        ]
    )
    (output / "robustness_report_zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.input)
    required = {
        "participant",
        "film_id",
        "emotion",
        "term_set",
        "dominance_orientation",
        *[f"{dim}_elicited" for dim in DIMS],
        *[f"{dim}_nrc" for dim in DIMS],
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    main = data[
        (data["term_set"] == "noun")
        & (data["dominance_orientation"] == "reported")
    ].copy()
    if len(main) != 414 or main["participant"].nunique() != 23 or main["emotion"].nunique() != 9:
        raise ValueError("Unexpected main analysis dimensions")

    permutations = np.asarray(list(itertools.permutations(range(9))), dtype=np.int16)
    exact = exact_tests(data, permutations)
    influence = influence_analysis(data)
    categories = category_table(main)
    global_test = global_configuration_test(categories, permutations)
    affine = affine_parameters(categories)
    residual = loeo_residuals(categories)
    rng = np.random.default_rng(SEED)
    correlation_ci, slope_ci, residual_ci = hierarchical_bootstrap(main, args.bootstrap, rng)
    affine = affine.merge(slope_ci, on="dimension")
    residual = residual.merge(residual_ci, on="emotion")

    exact.to_csv(args.output / "exact_permutation_tests.csv", index=False)
    influence.to_csv(args.output / "leave_one_emotion_out_influence.csv", index=False)
    affine.to_csv(args.output / "affine_scale_mapping.csv", index=False)
    residual.to_csv(args.output / "calibrated_residuals_with_ci.csv", index=False)
    correlation_ci.to_csv(args.output / "hierarchical_bootstrap_correlations.csv", index=False)
    pd.DataFrame([global_test]).to_csv(args.output / "global_configuration_test.csv", index=False)
    make_figures(categories, exact, influence, affine, residual, args.output)
    write_summary(exact, global_test, correlation_ci, affine, influence, residual, args.output)

    manifest = {
        "analysis": "DREAMER x NRC-VAD category-level robustness",
        "input": str(args.input.resolve()),
        "input_sha256": sha256(args.input),
        "participants": int(main["participant"].nunique()),
        "films": int(main["film_id"].nunique()),
        "emotions": int(main["emotion"].nunique()),
        "trials": int(len(main)),
        "exact_permutations": int(len(permutations)),
        "hierarchical_bootstrap_draws": int(args.bootstrap),
        "random_seed": SEED,
        "bootstrap_units": "participants and films nested within emotion",
    }
    (args.output / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
