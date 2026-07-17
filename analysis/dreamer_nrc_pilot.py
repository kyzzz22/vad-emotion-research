"""Align DREAMER elicited VAD with NRC-VAD and run physiology checks."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import signal, stats
from scipy.io import loadmat
import statsmodels.formula.api as smf

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DREAMER_FILE = ROOT / "DREAMER.mat"
NRC_FILE = (
    ROOT / "public_data" / "case_pilot" / "nrc_vad" / "extracted"
    / "NRC-VAD-Lexicon-v2.1" / "Unigrams"
    / "unigrams-NRC-VAD-Lexicon-v2.1.txt"
)
OUTPUT = ROOT / "public_data" / "dreamer_pilot" / "results"

FILMS = [
    (1, "Searching for Bobby Fischer", "calmness"),
    (2, "D.O.A.", "surprise"),
    (3, "The Hangover", "amusement"),
    (4, "The Ring", "fear"),
    (5, "300", "excitement"),
    (6, "National Lampoon's Van Wilder", "disgust"),
    (7, "Wall-E", "happiness"),
    (8, "Crash", "anger"),
    (9, "My Girl", "sadness"),
    (10, "The Fly", "disgust"),
    (11, "Pride and Prejudice", "calmness"),
    (12, "Modern Times", "amusement"),
    (13, "Remember the Titans", "happiness"),
    (14, "Gentleman's Agreement", "anger"),
    (15, "Psycho", "fear"),
    (16, "The Bourne Identity", "excitement"),
    (17, "The Shawshank Redemption", "sadness"),
    (18, "The Departed", "surprise"),
]
NOUN_TERMS = {emotion: emotion for _, _, emotion in FILMS}
ADJECTIVE_TERMS = {
    "calmness": "calm",
    "surprise": "surprised",
    "amusement": "amused",
    "fear": "afraid",
    "excitement": "excited",
    "disgust": "disgusted",
    "happiness": "happy",
    "anger": "angry",
    "sadness": "sad",
}
DIMS = ("valence", "arousal", "dominance")


def holm_adjust(values: pd.Series) -> pd.Series:
    p = values.to_numpy(dtype=float)
    order = np.argsort(p)
    adjusted = np.empty_like(p)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p) - rank) * p[index])
        adjusted[index] = min(running, 1.0)
    return pd.Series(adjusted, index=values.index)


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    draws = rng.choice(values, size=(10_000, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(draws, [0.025, 0.975]).astype(float))


def load_dreamer(path: Path) -> dict:
    dreamer = loadmat(path, simplify_cells=True)["DREAMER"]
    if dreamer["noOfSubjects"] != 23 or dreamer["noOfVideoSequences"] != 18:
        raise ValueError("Unexpected DREAMER dimensions")
    return dreamer


def load_nrc(path: Path) -> pd.DataFrame:
    nrc = pd.read_csv(path, sep="\t")
    required = set(NOUN_TERMS.values()) | set(ADJECTIVE_TERMS.values())
    selected = nrc[nrc["term"].isin(required)].copy()
    missing = required - set(selected["term"])
    if missing:
        raise ValueError(f"Missing NRC terms: {sorted(missing)}")
    return selected


def extract_ratings(dreamer: dict) -> pd.DataFrame:
    film_table = pd.DataFrame(FILMS, columns=["film_id", "film", "emotion"])
    rows = []
    for participant, subject in enumerate(dreamer["Data"], start=1):
        for trial in range(18):
            rows.append(
                {
                    "participant": participant,
                    "age": int(subject["Age"]),
                    "gender": subject["Gender"],
                    "film_id": trial + 1,
                    "valence_score": float(subject["ScoreValence"][trial]),
                    "arousal_score": float(subject["ScoreArousal"][trial]),
                    "dominance_score": float(subject["ScoreDominance"][trial]),
                }
            )
    ratings = pd.DataFrame(rows).merge(film_table, on="film_id", validate="many_to_one")
    for dim in DIMS:
        ratings[f"{dim}_elicited"] = (ratings[f"{dim}_score"] - 3.0) / 2.0
    return ratings


def align_ratings(ratings: pd.DataFrame, nrc: pd.DataFrame) -> pd.DataFrame:
    index = nrc.set_index("term")
    frames = []
    for term_set, mapping in (("noun", NOUN_TERMS), ("adjective", ADJECTIVE_TERMS)):
        for dominance_orientation in ("reported", "reversed"):
            frame = ratings.copy()
            frame["term_set"] = term_set
            frame["dominance_orientation"] = dominance_orientation
            frame["nrc_term"] = frame["emotion"].map(mapping)
            for dim in DIMS:
                frame[f"{dim}_nrc"] = frame["nrc_term"].map(index[dim])
            if dominance_orientation == "reversed":
                frame["dominance_elicited"] *= -1.0
            for dim in DIMS:
                frame[f"delta_{dim}"] = frame[f"{dim}_elicited"] - frame[f"{dim}_nrc"]
            frame["distance_va"] = np.hypot(frame["delta_valence"], frame["delta_arousal"])
            frame["distance_vad"] = np.sqrt(
                sum(np.square(frame[f"delta_{dim}"]) for dim in DIMS)
            )
            frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def category_summary(aligned: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260715)
    participant_category = (
        aligned.groupby(
            ["term_set", "dominance_orientation", "participant", "emotion", "nrc_term"],
            as_index=False,
        )
        .agg(
            **{
                f"{dim}_elicited": (f"{dim}_elicited", "mean") for dim in DIMS
            },
            **{f"{dim}_nrc": (f"{dim}_nrc", "first") for dim in DIMS},
        )
    )
    for dim in DIMS:
        participant_category[f"delta_{dim}"] = (
            participant_category[f"{dim}_elicited"] - participant_category[f"{dim}_nrc"]
        )
    participant_category["distance_va"] = np.hypot(
        participant_category["delta_valence"], participant_category["delta_arousal"]
    )
    participant_category["distance_vad"] = np.sqrt(
        sum(np.square(participant_category[f"delta_{dim}"]) for dim in DIMS)
    )

    rows = []
    for keys, frame in participant_category.groupby(
        ["term_set", "dominance_orientation", "emotion", "nrc_term"], sort=False
    ):
        term_set, orientation, emotion, term = keys
        row: dict[str, float | int | str] = {
            "term_set": term_set,
            "dominance_orientation": orientation,
            "emotion": emotion,
            "nrc_term": term,
            "n_participants": frame["participant"].nunique(),
        }
        for dim in DIMS:
            delta = frame[f"delta_{dim}"].to_numpy()
            row[f"{dim}_elicited_mean"] = frame[f"{dim}_elicited"].mean()
            row[f"{dim}_nrc"] = frame[f"{dim}_nrc"].iloc[0]
            row[f"delta_{dim}_mean"] = delta.mean()
            lo, hi = bootstrap_mean_ci(delta, rng)
            row[f"delta_{dim}_ci_low"] = lo
            row[f"delta_{dim}_ci_high"] = hi
            test = stats.ttest_1samp(delta, 0.0)
            row[f"p_{dim}"] = test.pvalue
            row[f"dz_{dim}"] = delta.mean() / delta.std(ddof=1)
        row["centroid_distance_va"] = float(
            np.hypot(row["delta_valence_mean"], row["delta_arousal_mean"])
        )
        row["centroid_distance_vad"] = float(
            np.sqrt(sum(row[f"delta_{dim}_mean"] ** 2 for dim in DIMS))
        )
        for distance in ("distance_va", "distance_vad"):
            values = frame[distance].to_numpy()
            lo, hi = bootstrap_mean_ci(values, rng)
            row[f"participant_mean_{distance}"] = values.mean()
            row[f"participant_mean_{distance}_ci_low"] = lo
            row[f"participant_mean_{distance}_ci_high"] = hi
        rows.append(row)

    summary = pd.DataFrame(rows)
    long_p = summary.melt(
        id_vars=["term_set", "dominance_orientation", "emotion"],
        value_vars=[f"p_{dim}" for dim in DIMS],
        var_name="dimension",
        value_name="p_raw",
    )
    long_p["p_holm"] = long_p.groupby(["term_set", "dominance_orientation"])[
        "p_raw"
    ].transform(holm_adjust)
    for dim in DIMS:
        adjusted = long_p[long_p["dimension"] == f"p_{dim}"][
            ["term_set", "dominance_orientation", "emotion", "p_holm"]
        ].rename(columns={"p_holm": f"p_{dim}_holm"})
        summary = summary.merge(
            adjusted,
            on=["term_set", "dominance_orientation", "emotion"],
            how="left",
        )
    return participant_category, summary.sort_values(
        ["term_set", "dominance_orientation", "centroid_distance_vad"]
    )


def rank_correlations(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (term_set, orientation), frame in summary.groupby(
        ["term_set", "dominance_orientation"]
    ):
        for dim in DIMS:
            x = frame[f"{dim}_nrc"].to_numpy()
            y = frame[f"{dim}_elicited_mean"].to_numpy()
            pearson = stats.pearsonr(x, y)
            spearman = stats.spearmanr(x, y)
            rows.append(
                {
                    "term_set": term_set,
                    "dominance_orientation": orientation,
                    "dimension": dim,
                    "n_emotions": len(frame),
                    "pearson_r": pearson.statistic,
                    "pearson_p": pearson.pvalue,
                    "spearman_rho": spearman.statistic,
                    "spearman_p": spearman.pvalue,
                }
            )
    return pd.DataFrame(rows)


def leave_one_emotion_out_calibration(summary: pd.DataFrame) -> pd.DataFrame:
    """Estimate emotion-specific residuals after cross-source affine calibration."""
    rows = []
    for (term_set, orientation), frame in summary.groupby(
        ["term_set", "dominance_orientation"]
    ):
        frame = frame.reset_index(drop=True)
        for held_out in range(len(frame)):
            keep = np.arange(len(frame)) != held_out
            row = {
                "term_set": term_set,
                "dominance_orientation": orientation,
                "emotion": frame.loc[held_out, "emotion"],
            }
            for dim in DIMS:
                x = frame[f"{dim}_nrc"].to_numpy()
                y = frame[f"{dim}_elicited_mean"].to_numpy()
                slope, intercept = np.polyfit(x[keep], y[keep], 1)
                prediction = intercept + slope * x[held_out]
                row[f"predicted_{dim}"] = prediction
                row[f"residual_{dim}"] = y[held_out] - prediction
                row[f"calibration_slope_{dim}"] = slope
                row[f"calibration_intercept_{dim}"] = intercept
            row["calibrated_residual_va"] = float(
                np.hypot(row["residual_valence"], row["residual_arousal"])
            )
            row["calibrated_residual_vad"] = float(
                np.sqrt(sum(row[f"residual_{dim}"] ** 2 for dim in DIMS))
            )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["term_set", "dominance_orientation", "calibrated_residual_vad"]
    )


def eeg_features(values: np.ndarray, fs: int, electrodes: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)[-60 * fs :]
    freqs, psd = signal.welch(values, fs=fs, nperseg=fs * 2, axis=0)
    total_mask = (freqs >= 4) & (freqs <= 30)
    total = np.trapezoid(psd[total_mask], freqs[total_mask], axis=0)
    features = {}
    for name, low, high in (("theta", 4, 8), ("alpha", 8, 13), ("beta", 13, 30)):
        mask = (freqs >= low) & (freqs < high)
        power = np.trapezoid(psd[mask], freqs[mask], axis=0)
        features[f"eeg_{name}_relative"] = float(np.mean(power / total))
    electrode_index = {name: i for i, name in enumerate(electrodes)}
    alpha_mask = (freqs >= 8) & (freqs < 13)
    alpha = np.trapezoid(psd[alpha_mask], freqs[alpha_mask], axis=0)
    left = np.mean([alpha[electrode_index[name]] for name in ("AF3", "F3")])
    right = np.mean([alpha[electrode_index[name]] for name in ("AF4", "F4")])
    features["eeg_frontal_alpha_asymmetry"] = float(np.log(right) - np.log(left))
    return features


def ecg_features(values: np.ndarray, fs: int) -> dict[str, float]:
    ecg = np.asarray(values, dtype=float)[-60 * fs :, 0]
    sos = signal.butter(3, [0.5, 40], btype="bandpass", fs=fs, output="sos")
    filtered = signal.sosfiltfilt(sos, ecg)
    prominence = max(np.std(filtered) * 0.5, np.finfo(float).eps)
    peaks, _ = signal.find_peaks(filtered, distance=int(0.3 * fs), prominence=prominence)
    rr = np.diff(peaks) / fs
    rr = rr[(rr >= 0.35) & (rr <= 1.5)]
    if len(rr) < 5:
        return {"ecg_hr_bpm": np.nan, "ecg_rmssd_ms": np.nan, "ecg_sdnn_ms": np.nan}
    return {
        "ecg_hr_bpm": float(60.0 / rr.mean()),
        "ecg_rmssd_ms": float(np.sqrt(np.mean(np.diff(rr) ** 2)) * 1000.0),
        "ecg_sdnn_ms": float(np.std(rr, ddof=1) * 1000.0),
    }


def extract_physiology(dreamer: dict) -> pd.DataFrame:
    rows = []
    eeg_fs = int(dreamer["EEG_SamplingRate"])
    ecg_fs = int(dreamer["ECG_SamplingRate"])
    electrodes = np.asarray(dreamer["EEG_Electrodes"])
    film_table = pd.DataFrame(FILMS, columns=["film_id", "film", "emotion"])
    for participant, subject in enumerate(dreamer["Data"], start=1):
        for trial in range(18):
            row = {"participant": participant, "film_id": trial + 1}
            for modality, extractor, fs in (
                ("EEG", lambda x: eeg_features(x, eeg_fs, electrodes), eeg_fs),
                ("ECG", lambda x: ecg_features(x, ecg_fs), ecg_fs),
            ):
                baseline = extractor(subject[modality]["baseline"][trial])
                stimulus = extractor(subject[modality]["stimuli"][trial])
                for feature in stimulus:
                    row[f"{feature}_delta"] = stimulus[feature] - baseline[feature]
            rows.append(row)
    return pd.DataFrame(rows).merge(film_table, on="film_id", validate="many_to_one")


def physiology_regressions(aligned: pd.DataFrame, physiology: pd.DataFrame) -> pd.DataFrame:
    main = aligned[
        (aligned["term_set"] == "noun")
        & (aligned["dominance_orientation"] == "reported")
    ].copy()
    data = main.merge(physiology, on=["participant", "film_id", "film", "emotion"])
    feature_columns = [column for column in physiology if column.endswith("_delta")]
    rows = []
    for feature in feature_columns:
        frame = data[["distance_vad", "participant", "film_id", feature]].dropna().copy()
        frame["feature_z"] = (frame[feature] - frame[feature].mean()) / frame[feature].std(ddof=1)
        model = smf.ols("distance_vad ~ feature_z + C(film_id)", data=frame).fit(
            cov_type="cluster", cov_kwds={"groups": frame["participant"]}
        )
        rows.append(
            {
                "feature": feature,
                "n_trials": len(frame),
                "beta": model.params["feature_z"],
                "se_clustered": model.bse["feature_z"],
                "p_raw": model.pvalues["feature_z"],
                "ci_low": model.conf_int().loc["feature_z", 0],
                "ci_high": model.conf_int().loc["feature_z", 1],
            }
        )
    result = pd.DataFrame(rows)
    result["p_holm"] = holm_adjust(result["p_raw"])
    return result.sort_values("p_holm")


def make_figures(summary: pd.DataFrame, calibration: pd.DataFrame, output: Path) -> None:
    main = summary[
        (summary["term_set"] == "noun")
        & (summary["dominance_orientation"] == "reported")
    ].sort_values("centroid_distance_vad")
    colors = plt.cm.Set2(np.linspace(0, 1, len(main)))

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.5), sharex=True, sharey=True)
    for ax, dim in zip(axes, DIMS):
        ax.plot([-1, 1], [-1, 1], color="#AEB4BA", linewidth=1)
        for color, (_, row) in zip(colors, main.iterrows()):
            ax.scatter(row[f"{dim}_nrc"], row[f"{dim}_elicited_mean"], color=color, s=55)
            ax.annotate(row["emotion"], (row[f"{dim}_nrc"], row[f"{dim}_elicited_mean"]), xytext=(3, 4), textcoords="offset points", fontsize=8)
        ax.set_title(dim.capitalize())
        ax.set_xlabel("NRC lexical score")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
    axes[0].set_ylabel("DREAMER elicited mean")
    fig.suptitle("Lexical norms versus elicited experience")
    fig.tight_layout()
    fig.savefig(output / "dreamer_nrc_dimension_scatter.png", dpi=220, facecolor="white")
    plt.close(fig)

    calibrated = calibration[
        (calibration["term_set"] == "noun")
        & (calibration["dominance_orientation"] == "reported")
    ][["emotion", "calibrated_residual_vad"]]
    ordered = main.merge(calibrated, on="emotion").sort_values("centroid_distance_vad")
    fig, ax = plt.subplots(figsize=(8, 5.2))
    y = np.arange(len(ordered))
    ax.barh(y - 0.18, ordered["centroid_distance_vad"], height=0.34, color="#377D71", label="Raw coordinate distance")
    ax.barh(y + 0.18, ordered["calibrated_residual_vad"], height=0.34, color="#D49B31", label="LOEO calibrated residual")
    ax.set_yticks(y)
    ax.set_yticklabels(ordered["emotion"].tolist())
    ax.invert_yaxis()
    ax.set_xlabel("Euclidean discrepancy in VAD")
    ax.set_title("DREAMER–NRC discrepancy by target emotion")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output / "dreamer_nrc_vad_distance.png", dpi=220, facecolor="white")
    plt.close(fig)


def write_report(
    summary: pd.DataFrame,
    correlations: pd.DataFrame,
    calibration: pd.DataFrame,
    physiology_models: pd.DataFrame,
    output: Path,
) -> None:
    main = summary[
        (summary["term_set"] == "noun")
        & (summary["dominance_orientation"] == "reported")
    ].sort_values("centroid_distance_vad")
    reverse = summary[
        (summary["term_set"] == "noun")
        & (summary["dominance_orientation"] == "reversed")
    ].sort_values("centroid_distance_vad")
    corr_main = correlations[
        (correlations["term_set"] == "noun")
        & (correlations["dominance_orientation"] == "reported")
    ]
    calibrated = calibration[
        (calibration["term_set"] == "noun")
        & (calibration["dominance_orientation"] == "reported")
    ].set_index("emotion")
    lines = [
        "# DREAMER × NRC-VAD 三维复跑报告",
        "",
        "## 数据与设计",
        "",
        "- DREAMER v1.0.2：23名被试 × 18段影片 = 414个试次。",
        "- 9种目标情绪，每种由两段影片诱发。",
        "- DREAMER 1–5分按 `(score-3)/2` 映射到 NRC v2.1 的 −1–1。",
        "- 主词项使用目标情绪名词；状态形容词和 Dominance 反向编码为敏感性分析。",
        "- 置信区间在参与者层面聚类自助抽样；刺激仅两段/情绪，不能充分估计刺激总体误差。",
        "",
        "## 主结果：三维中心距离",
        "",
        "| 排名 | 情绪 | DREAMER V/A/D | NRC V/A/D | 原始中心距离 | 校准残差 | 参与者平均距离及95%CI |",
        "|---:|---|---|---|---:|---:|---|",
    ]
    for rank, (_, row) in enumerate(main.iterrows(), start=1):
        lines.append(
            f"| {rank} | {row['emotion']} | "
            f"{row['valence_elicited_mean']:.3f}/{row['arousal_elicited_mean']:.3f}/{row['dominance_elicited_mean']:.3f} | "
            f"{row['valence_nrc']:.3f}/{row['arousal_nrc']:.3f}/{row['dominance_nrc']:.3f} | "
            f"{row['centroid_distance_vad']:.3f} | "
            f"{calibrated.loc[row['emotion'], 'calibrated_residual_vad']:.3f} | "
            f"{row['participant_mean_distance_vad']:.3f} "
            f"[{row['participant_mean_distance_vad_ci_low']:.3f}, {row['participant_mean_distance_vad_ci_high']:.3f}] |"
        )
    lines.extend(["", "## 类别层面对应关系", ""])
    for _, row in corr_main.iterrows():
        lines.append(
            f"- {row['dimension'].capitalize()}：Pearson r={row['pearson_r']:.3f} "
            f"(p={row['pearson_p']:.3g})；Spearman ρ={row['spearman_rho']:.3f} "
            f"(p={row['spearman_p']:.3g})。"
        )
    lines.extend(
        [
            "",
            "相关分析的有效样本是9种情绪，不是414个试次，应视为小样本类别层面的证据。",
            "",
            "## 控制量表压缩后的偏离",
            "",
            "为区分全局尺度平移/压缩和情绪特异差异，对每种情绪执行留一法：用其余8种情绪分别拟合 NRC→DREAMER 的线性映射，再预测被留出的情绪。",
            "",
            "| 排名 | 情绪 | 校准后VA残差 | 校准后VAD残差 |",
            "|---:|---|---:|---:|",
        ]
    )
    for rank, (_, row) in enumerate(
        calibrated.reset_index().sort_values("calibrated_residual_vad").iterrows(), start=1
    ):
        lines.append(
            f"| {rank} | {row['emotion']} | {row['calibrated_residual_va']:.3f} | "
            f"{row['calibrated_residual_vad']:.3f} |"
        )
    lines.extend(
        [
            "",
            "原始距离回答绝对坐标是否重合；校准残差回答去除数据库整体尺度差异后，哪些情绪仍异常偏离。留一法避免用被评估情绪本身拟合校准线。",
            "",
            "## Dominance 方向敏感性",
            "",
            f"- 按数据报告方向，9类平均中心距离为 {main['centroid_distance_vad'].mean():.3f}。",
            f"- 将体验 Dominance 反向后，平均中心距离为 {reverse['centroid_distance_vad'].mean():.3f}。",
            "- 两种结果均保留；在确认原始 SAM 图示的编码方向前，不把 D 的正负偏差解释为心理机制。",
            "",
            "## 生理信号探索",
            "",
            "EEG/ECG 使用刺激和对应基线的最后60秒。回归控制18段影片固定效应，标准误按被试聚类。",
            "",
            "| 特征 | beta | 95% CI | Holm p |",
            "|---|---:|---|---:|",
        ]
    )
    for _, row in physiology_models.iterrows():
        lines.append(
            f"| {row['feature']} | {row['beta']:.3f} | "
            f"[{row['ci_low']:.3f}, {row['ci_high']:.3f}] | {row['p_holm']:.3g} |"
        )
    lines.extend(
        [
            "",
            "生理回归是探索性分析，不能把相关特征解释为产生 VAD 或证明客观情绪坐标。",
            "",
            "## 数据来源",
            "",
            "- Katsigiannis & Ramzan (2018), DOI: 10.1109/JBHI.2017.2688239。",
            "- 影片目标情绪映射来自原论文 Table I；每种情绪两段影片。",
            "- NRC-VAD v2.1 仅限非商业研究/教育使用，禁止再分发。",
        ]
    )
    (output / "DREAMER_NRC_复跑报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    dreamer = load_dreamer(DREAMER_FILE)
    nrc = load_nrc(NRC_FILE)
    ratings = extract_ratings(dreamer)
    aligned = align_ratings(ratings, nrc)
    participant_category, summary = category_summary(aligned)
    correlations = rank_correlations(summary)
    calibration = leave_one_emotion_out_calibration(summary)
    physiology = extract_physiology(dreamer)
    physiology_models = physiology_regressions(aligned, physiology)

    ratings.to_csv(OUTPUT / "dreamer_trial_ratings.csv", index=False)
    aligned.to_csv(OUTPUT / "dreamer_trial_alignment_all_sensitivities.csv", index=False)
    participant_category.to_csv(OUTPUT / "dreamer_participant_category_alignment.csv", index=False)
    summary.to_csv(OUTPUT / "dreamer_category_summary.csv", index=False)
    correlations.to_csv(OUTPUT / "dreamer_category_correlations.csv", index=False)
    calibration.to_csv(OUTPUT / "dreamer_leave_one_emotion_out_calibration.csv", index=False)
    physiology.to_csv(OUTPUT / "dreamer_physiology_features.csv", index=False)
    physiology_models.to_csv(OUTPUT / "dreamer_physiology_models.csv", index=False)
    make_figures(summary, calibration, OUTPUT)
    write_report(summary, correlations, calibration, physiology_models, OUTPUT)

    manifest = {
        "dreamer_version": dreamer["Version"],
        "participants": ratings["participant"].nunique(),
        "films": ratings["film_id"].nunique(),
        "emotions": ratings["emotion"].nunique(),
        "trials": len(ratings),
        "eeg_sampling_rate": int(dreamer["EEG_SamplingRate"]),
        "ecg_sampling_rate": int(dreamer["ECG_SamplingRate"]),
        "random_seed": 20260715,
        "scale_transform": "(score - 3) / 2",
    }
    (OUTPUT / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
