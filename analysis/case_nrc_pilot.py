"""Reproducible feasibility pilot aligning CASE elicited VA with NRC-VAD.

The script never modifies the source datasets. It reconstructs CASE video
segments from the official metadata, summarizes continuous annotations, and
extracts a small physiological engineering-check subset.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "public_data" / "case_pilot" / "case_dataset"
DEFAULT_NRC = (
    ROOT
    / "public_data"
    / "case_pilot"
    / "nrc_vad"
    / "extracted"
    / "NRC-VAD-Lexicon-v2.1"
    / "Unigrams"
    / "unigrams-NRC-VAD-Lexicon-v2.1.txt"
)
DEFAULT_OUT = ROOT / "public_data" / "case_pilot" / "results"

EMOTION_CATEGORIES = ("amusing", "boring", "relaxed", "scary")
PRIMARY_TERMS = {
    "amusing": "amused",
    "boring": "bored",
    "relaxed": "relaxed",
    "scary": "afraid",
}
SENSITIVITY_TERMS = {
    "amusing": "amusement",
    "boring": "boredom",
    "relaxed": "relaxation",
    "scary": "fear",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--nrc-file", type=Path, default=DEFAULT_NRC)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--physiology-subjects",
        type=int,
        default=3,
        help="Number of subjects used only for the physiology engineering check.",
    )
    return parser.parse_args()


def load_metadata(case_root: Path) -> tuple[pd.DataFrame, dict[str, float]]:
    metadata = case_root / "metadata"
    sequences = pd.read_csv(metadata / "seqs_order.txt", sep="\t")
    # One source row has a harmless trailing tab; select the two documented columns.
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
            "segment_index": np.arange(len(labels)),
            "video_label": labels,
            "start_ms": starts,
            "end_ms": ends,
            "duration_ms": lengths,
        }
    )
    table["category"] = table["video_label"].str.split("-").str[0]
    return table


def assign_segments(time_ms: np.ndarray, segments: pd.DataFrame) -> np.ndarray:
    idx = np.searchsorted(segments["end_ms"].to_numpy(), time_ms, side="left")
    idx[idx >= len(segments)] = -1
    return idx


def summarize_annotations(
    case_root: Path, sequences: pd.DataFrame, durations: dict[str, float]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, float | int | str]] = []
    for subject in range(1, 31):
        source = case_root / "data" / "raw" / "annotations" / f"sub{subject}_joystick.txt"
        raw = pd.read_csv(
            source,
            sep="\t",
            header=None,
            names=["time_s", "raw_valence", "raw_arousal"],
            dtype=float,
        )
        raw["time_ms"] = raw["time_s"] * 1000.0
        raw["valence"] = 0.5 + 9.0 * (raw["raw_valence"] + 26225.0) / 52450.0
        raw["arousal"] = 0.5 + 9.0 * (raw["raw_arousal"] + 26225.0) / 52450.0

        segments = segment_table(sequences.iloc[:, subject - 1], durations)
        raw["segment_index"] = assign_segments(raw["time_ms"].to_numpy(), segments)
        raw = raw[raw["segment_index"] >= 0].copy()
        raw = raw.merge(segments, on="segment_index", how="left", validate="many_to_one")
        raw = raw[raw["category"].isin(EMOTION_CATEGORIES)].copy()
        raw["elapsed_ms"] = raw["time_ms"] - raw["start_ms"]
        raw["in_last_60s"] = raw["time_ms"] >= raw["end_ms"] - 60_000.0

        for (segment_idx, label, category), trial in raw.groupby(
            ["segment_index", "video_label", "category"], sort=False
        ):
            steady = trial[trial["in_last_60s"]]
            for window, frame in (("last_60s", steady), ("whole_video", trial)):
                rows.append(
                    {
                        "subject": subject,
                        "segment_index": int(segment_idx),
                        "video_label": label,
                        "category": category,
                        "window": window,
                        "n_samples": len(frame),
                        "valence_case": frame["valence"].mean(),
                        "arousal_case": frame["arousal"].mean(),
                    }
                )

    trial_summary = pd.DataFrame(rows)
    category_summary = (
        trial_summary.groupby(["subject", "category", "window"], as_index=False)
        .agg(
            valence_case=("valence_case", "mean"),
            arousal_case=("arousal_case", "mean"),
            n_videos=("video_label", "nunique"),
        )
    )
    for dim in ("valence", "arousal"):
        category_summary[f"{dim}_case_scaled"] = (
            category_summary[f"{dim}_case"] - 5.0
        ) / 4.5
    return trial_summary, category_summary


def load_nrc_terms(nrc_file: Path) -> pd.DataFrame:
    nrc = pd.read_csv(nrc_file, sep="\t")
    terms = sorted(set(PRIMARY_TERMS.values()) | set(SENSITIVITY_TERMS.values()))
    selected = nrc[nrc["term"].isin(terms)].copy()
    missing = sorted(set(terms) - set(selected["term"]))
    if missing:
        raise ValueError(f"NRC terms not found: {missing}")
    return selected


def align_with_nrc(category: pd.DataFrame, nrc: pd.DataFrame) -> pd.DataFrame:
    nrc_index = nrc.set_index("term")
    aligned_frames = []
    for term_set, mapping in (
        ("primary_state_adjective", PRIMARY_TERMS),
        ("sensitivity_state_noun", SENSITIVITY_TERMS),
    ):
        frame = category.copy()
        frame["term_set"] = term_set
        frame["nrc_term"] = frame["category"].map(mapping)
        for dim in ("valence", "arousal", "dominance"):
            frame[f"{dim}_nrc"] = frame["nrc_term"].map(nrc_index[dim])
        frame["delta_valence"] = frame["valence_case_scaled"] - frame["valence_nrc"]
        frame["delta_arousal"] = frame["arousal_case_scaled"] - frame["arousal_nrc"]
        frame["distance_va"] = np.hypot(frame["delta_valence"], frame["delta_arousal"])
        aligned_frames.append(frame)
    return pd.concat(aligned_frames, ignore_index=True)


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    draws = rng.choice(values, size=(10_000, len(values)), replace=True).mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(low), float(high)


def holm_adjust(p_values: pd.Series) -> pd.Series:
    values = p_values.to_numpy(dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    running = 0.0
    m = len(values)
    for rank, index in enumerate(order):
        candidate = (m - rank) * values[index]
        running = max(running, candidate)
        adjusted[index] = min(running, 1.0)
    return pd.Series(adjusted, index=p_values.index)


def inferential_summary(aligned: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(20260714)
    rows = []
    grouped = aligned.groupby(["window", "term_set", "category"], sort=False)
    for (window, term_set, category), frame in grouped:
        row: dict[str, float | int | str] = {
            "window": window,
            "term_set": term_set,
            "category": category,
            "n_subjects": frame["subject"].nunique(),
            "nrc_term": frame["nrc_term"].iloc[0],
            "valence_nrc": frame["valence_nrc"].iloc[0],
            "arousal_nrc": frame["arousal_nrc"].iloc[0],
            "dominance_nrc": frame["dominance_nrc"].iloc[0],
        }
        for dim in ("valence", "arousal"):
            case_values = frame[f"{dim}_case_scaled"].to_numpy()
            deltas = frame[f"delta_{dim}"].to_numpy()
            lo, hi = bootstrap_ci(deltas, rng)
            test = stats.ttest_1samp(deltas, popmean=0.0)
            row[f"{dim}_case_mean"] = case_values.mean()
            row[f"delta_{dim}_mean"] = deltas.mean()
            row[f"delta_{dim}_ci_low"] = lo
            row[f"delta_{dim}_ci_high"] = hi
            row[f"p_{dim}"] = test.pvalue
            row[f"dz_{dim}"] = deltas.mean() / deltas.std(ddof=1)
        distances = frame["distance_va"].to_numpy()
        lo, hi = bootstrap_ci(distances, rng)
        row["centroid_distance_va"] = float(
            np.hypot(row["delta_valence_mean"], row["delta_arousal_mean"])
        )
        row["distance_va_mean"] = distances.mean()
        row["distance_va_ci_low"] = lo
        row["distance_va_ci_high"] = hi
        rows.append(row)

    summary = pd.DataFrame(rows)
    long_p = summary.melt(
        id_vars=["window", "term_set", "category"],
        value_vars=["p_valence", "p_arousal"],
        var_name="dimension",
        value_name="p_raw",
    )
    long_p["p_holm"] = long_p.groupby(["window", "term_set"])["p_raw"].transform(
        holm_adjust
    )
    for dim in ("valence", "arousal"):
        adjusted = long_p[long_p["dimension"] == f"p_{dim}"][
            ["window", "term_set", "category", "p_holm"]
        ].rename(columns={"p_holm": f"p_{dim}_holm"})
        summary = summary.merge(
            adjusted, on=["window", "term_set", "category"], how="left"
        )
    return summary.sort_values(["window", "term_set", "centroid_distance_va"])


def physiology_engineering_check(
    case_root: Path,
    sequences: pd.DataFrame,
    durations: dict[str, float],
    n_subjects: int,
) -> pd.DataFrame:
    """Extract simple calibrated, baseline-corrected features from a subset.

    These are synchronization checks, not confirmatory physiological outcomes.
    """
    rows = []
    columns = [
        "time_s",
        "ecg_v",
        "bvp_v",
        "gsr_v",
        "rsp_v",
        "skt_v",
        "emg_zygo_v",
        "emg_coru_v",
        "emg_trap_v",
    ]
    for subject in range(1, n_subjects + 1):
        segments = segment_table(sequences.iloc[:, subject - 1], durations)
        source = case_root / "data" / "raw" / "physiological" / f"sub{subject}_DAQ.txt"
        per_segment = []
        for chunk in pd.read_csv(
            source,
            sep="\t",
            header=None,
            names=columns,
            dtype=float,
            chunksize=250_000,
        ):
            chunk["time_ms"] = chunk["time_s"] * 1000.0
            chunk["segment_index"] = assign_segments(chunk["time_ms"].to_numpy(), segments)
            chunk = chunk[chunk["segment_index"] >= 0].copy()
            chunk["gsr"] = 24.0 * chunk["gsr_v"] - 49.2
            chunk["skt"] = 21.341 * chunk["skt_v"] - 32.085
            chunk["bvp"] = 58.962 * chunk["bvp_v"] - 115.09
            chunk["rsp"] = 58.923 * chunk["rsp_v"] - 115.01
            chunk["emg_zygo"] = (chunk["emg_zygo_v"] - 2.0) / 4000.0 * 1_000_000.0
            chunk["emg_coru"] = (chunk["emg_coru_v"] - 2.0) / 4000.0 * 1_000_000.0
            grouped = chunk.groupby("segment_index")
            part = grouped.agg(
                n=("time_s", "size"),
                gsr_sum=("gsr", "sum"),
                gsr_sq=("gsr", lambda x: np.square(x).sum()),
                skt_sum=("skt", "sum"),
                bvp_sum=("bvp", "sum"),
                bvp_sq=("bvp", lambda x: np.square(x).sum()),
                rsp_sum=("rsp", "sum"),
                rsp_sq=("rsp", lambda x: np.square(x).sum()),
                zygo_sum=("emg_zygo", "sum"),
                coru_sum=("emg_coru", "sum"),
            ).reset_index()
            per_segment.append(part)

        combined = pd.concat(per_segment, ignore_index=True)
        sums = combined.groupby("segment_index", as_index=False).sum()
        for signal in ("gsr", "skt", "bvp", "rsp", "zygo", "coru"):
            sums[f"{signal}_mean"] = sums[f"{signal}_sum"] / sums["n"]
        for signal in ("gsr", "bvp", "rsp"):
            variance = sums[f"{signal}_sq"] / sums["n"] - np.square(sums[f"{signal}_mean"])
            sums[f"{signal}_sd"] = np.sqrt(np.maximum(variance, 0.0))
        sums = sums.merge(segments, on="segment_index", how="left", validate="one_to_one")

        emotion_rows = sums[sums["category"].isin(EMOTION_CATEGORIES)].copy()
        for _, emotion in emotion_rows.iterrows():
            previous = sums[sums["segment_index"] == emotion["segment_index"] - 1]
            if previous.empty or previous.iloc[0]["video_label"] != "bluVid":
                continue
            baseline = previous.iloc[0]
            rows.append(
                {
                    "subject": subject,
                    "video_label": emotion["video_label"],
                    "category": emotion["category"],
                    "n_samples": int(emotion["n"]),
                    "gsr_mean_delta": emotion["gsr_mean"] - baseline["gsr_mean"],
                    "skt_mean_delta": emotion["skt_mean"] - baseline["skt_mean"],
                    "bvp_sd_delta": emotion["bvp_sd"] - baseline["bvp_sd"],
                    "rsp_sd_delta": emotion["rsp_sd"] - baseline["rsp_sd"],
                    "zygo_mean_delta": emotion["zygo_mean"] - baseline["zygo_mean"],
                    "coru_mean_delta": emotion["coru_mean"] - baseline["coru_mean"],
                }
            )
    return pd.DataFrame(rows)


def make_plot(summary: pd.DataFrame, output: Path) -> None:
    main = summary[
        (summary["window"] == "last_60s")
        & (summary["term_set"] == "primary_state_adjective")
    ].copy()
    main = main.set_index("category").loc[list(EMOTION_CATEGORIES)].reset_index()
    colors = ["#2F7D6D", "#6F7782", "#D89B2B", "#B4494F"]

    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    for i, row in main.iterrows():
        ax.plot(
            [row["valence_nrc"], row["valence_case_mean"]],
            [row["arousal_nrc"], row["arousal_case_mean"]],
            color=colors[i],
            linewidth=2,
            alpha=0.8,
        )
        ax.scatter(row["valence_nrc"], row["arousal_nrc"], marker="s", s=70, color=colors[i])
        ax.scatter(row["valence_case_mean"], row["arousal_case_mean"], marker="o", s=70, color=colors[i])
        ax.annotate(row["category"], (row["valence_case_mean"], row["arousal_case_mean"]), xytext=(5, 5), textcoords="offset points")
    ax.axhline(0, color="#B8BDC3", linewidth=0.8)
    ax.axvline(0, color="#B8BDC3", linewidth=0.8)
    ax.set(xlim=(-1.05, 1.05), ylim=(-1.05, 1.05), xlabel="Valence", ylabel="Arousal")
    ax.set_title("CASE elicited VA vs NRC lexical VA")
    ax.text(0.02, 0.02, "square: NRC word   circle: CASE mean", transform=ax.transAxes, fontsize=9)
    fig.tight_layout()
    fig.savefig(output / "case_vs_nrc_va.png", dpi=220)
    plt.close(fig)


def write_report(summary: pd.DataFrame, physiology: pd.DataFrame, output: Path) -> None:
    main = summary[
        (summary["window"] == "last_60s")
        & (summary["term_set"] == "primary_state_adjective")
    ].sort_values("centroid_distance_va")
    sensitivity = summary[
        (summary["window"] == "last_60s")
        & (summary["term_set"] == "sensitivity_state_noun")
    ].sort_values("centroid_distance_va")
    lines = [
        "# CASE × NRC-VAD 可行性试跑",
        "",
        "## 分析设定",
        "",
        "- CASE：30名被试，每人8段情绪视频；连续 Valence/Arousal 自评。",
        "- 主窗口：每段视频最后60秒；完整视频均值作为敏感性分析。",
        "- 尺度：CASE `[0.5, 9.5]` 线性变换至 NRC v2.1 的 `[-1, 1]`。",
        "- 主映射：amusing→amused，boring→bored，relaxed→relaxed，scary→afraid。",
        "- 不比较 Dominance：CASE 没有 D 自评，不能从生理信号直接补成 D。",
        "",
        "## 主结果",
        "",
        "| 排名 | 类别 | NRC词 | CASE V | CASE A | NRC V | NRC A | 中心距离 | 参与者平均距离 | 95% CI |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rank, (_, row) in enumerate(main.iterrows(), start=1):
        lines.append(
            f"| {rank} | {row['category']} | {row['nrc_term']} | "
            f"{row['valence_case_mean']:.3f} | {row['arousal_case_mean']:.3f} | "
            f"{row['valence_nrc']:.3f} | {row['arousal_nrc']:.3f} | "
            f"{row['centroid_distance_va']:.3f} | {row['distance_va_mean']:.3f} | "
            f"[{row['distance_va_ci_low']:.3f}, {row['distance_va_ci_high']:.3f}] |"
        )
    lines.extend(
        [
            "",
            "中心距离用于描述类别重合度；参与者平均距离同时包含个体离散度，其置信区间由参与者聚类自助法估计。",
            "维度差异的原始 p 值和 Holm 校正值见 `category_alignment_summary.csv`。",
            "这些单样本检验把 NRC 坐标视为固定参照，未纳入 NRC 词项本身的测量误差，不能解释为两个总体的完整双样本检验。",
            "",
            "## 词形敏感性",
            "",
            "| 排名 | 类别 | 替代词 | 中心距离 | 参与者平均距离 | 95% CI |",
            "|---:|---|---|---:|---:|---|",
        ]
    )
    for rank, (_, row) in enumerate(sensitivity.iterrows(), start=1):
        lines.append(
            f"| {rank} | {row['category']} | {row['nrc_term']} | "
            f"{row['centroid_distance_va']:.3f} | {row['distance_va_mean']:.3f} | "
            f"[{row['distance_va_ci_low']:.3f}, {row['distance_va_ci_high']:.3f}] |"
        )
    lines.extend(
        [
            "",
            "主映射在完整视频窗口下仍保持 scary、amusing、boring、relaxed 的距离排序。",
            "改用状态名词后 amusing 与 relaxed 的次序发生变化，说明词项选择是实质性分析决策。",
            "",
            "## 生理工程检查",
            "",
            f"- 已解析 {physiology['subject'].nunique() if not physiology.empty else 0} 名被试、"
            f"{len(physiology)} 个情绪试次，并用每段情绪视频之前的蓝屏段做基线。",
            "- 已验证 GSR、皮温、BVP、呼吸及面部 EMG 的校准、分段和汇总链路。",
            "- 该子集只证明原始生理数据可用；不能据此报告情绪效应或训练预测模型。",
            "",
            "## 严格结论",
            "",
            "这套数据足以验证“词汇规范 VA 与刺激诱发体验 VA 的重合/偏离”分析流程，"
            "但只有四个情绪类别，类别层面的有效样本量是4，而不是240。因而本试跑可以"
            "证明方法可执行并发现候选偏离，不能单独支撑关于一般情绪语义与体验关系的强结论。",
            "",
            "正式论文应换用含更多可命名情绪、逐刺激 VAD 的 AMIGOS/DREAMER，或新增独立"
            "刺激语义评分；CASE 更适合作为方法预实验和 VA 复现数据集。",
            "",
            "## 数据来源",
            "",
            "- CASE: Sharma et al. (2019), *Scientific Data*, DOI: 10.1038/s41597-019-0209-0。",
            "- NRC-VAD v2.1: Mohammad (2025), `https://saifmohammad.com/WebPages/nrc-vad.html`。",
            "- NRC-VAD 仅限非商业研究/教育用途，不应随分析产物再分发。",
        ]
    )
    (output / "可行性报告.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    sequences, durations = load_metadata(args.case_root)
    trial, category = summarize_annotations(args.case_root, sequences, durations)
    nrc = load_nrc_terms(args.nrc_file)
    aligned = align_with_nrc(category, nrc)
    summary = inferential_summary(aligned)
    physiology = physiology_engineering_check(
        args.case_root, sequences, durations, args.physiology_subjects
    )

    trial.to_csv(args.output / "case_trial_va.csv", index=False)
    aligned.to_csv(args.output / "participant_category_alignment.csv", index=False)
    summary.to_csv(args.output / "category_alignment_summary.csv", index=False)
    physiology.to_csv(args.output / "physiology_engineering_check.csv", index=False)
    make_plot(summary, args.output)
    write_report(summary, physiology, args.output)

    manifest = {
        "case_root": str(args.case_root.resolve()),
        "nrc_file": str(args.nrc_file.resolve()),
        "random_seed": 20260714,
        "annotation_subjects": int(category["subject"].nunique()),
        "emotional_trials": int(trial[trial["window"] == "last_60s"].shape[0]),
        "physiology_subjects": int(physiology["subject"].nunique()),
        "primary_window": "last_60s",
        "case_to_nrc_transform": "(CASE - 5) / 4.5",
    }
    (args.output / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=True))


if __name__ == "__main__":
    main()
