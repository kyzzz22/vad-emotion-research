"""Create a reader-friendly DREAMER versus NRC-VAD comparison dashboard."""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "public_data" / "dreamer_pilot" / "results"
FONT_FILE = Path(r"C:\Windows\Fonts\NotoSansSC-VF.ttf")

CHINESE_NAMES = {
    "happiness": "幸福",
    "excitement": "兴奋",
    "anger": "愤怒",
    "calmness": "平静",
    "amusement": "欢乐",
    "fear": "恐惧",
    "surprise": "惊讶",
    "disgust": "厌恶",
    "sadness": "悲伤",
}


def main() -> None:
    font_manager.fontManager.addfont(FONT_FILE)
    family = font_manager.FontProperties(fname=FONT_FILE).get_name()
    plt.rcParams.update(
        {
            "font.family": family,
            "axes.unicode_minus": False,
            "font.size": 11,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    summary = pd.read_csv(RESULTS / "dreamer_category_summary.csv")
    calibration = pd.read_csv(RESULTS / "dreamer_leave_one_emotion_out_calibration.csv")
    main = summary[
        (summary["term_set"] == "noun")
        & (summary["dominance_orientation"] == "reported")
    ].copy()
    calibrated = calibration[
        (calibration["term_set"] == "noun")
        & (calibration["dominance_orientation"] == "reported")
    ][["emotion", "calibrated_residual_vad"]]
    data = (
        main.merge(calibrated, on="emotion")
        .sort_values("centroid_distance_vad")
        .reset_index(drop=True)
    )
    data["label"] = data["emotion"].map(CHINESE_NAMES) + "  " + data["emotion"]
    y = np.arange(len(data))

    fig = plt.figure(figsize=(16, 9.5), constrained_layout=False)
    grid = fig.add_gridspec(
        1, 4, left=0.15, right=0.97, top=0.80, bottom=0.16,
        width_ratios=[1, 1, 1, 1.20], wspace=0.12
    )
    axes = [fig.add_subplot(grid[0, i]) for i in range(4)]

    lexical_color = "#5E6670"
    elicited_color = "#16857B"
    connector_color = "#BAC1C7"
    raw_color = "#397D71"
    calibrated_color = "#D69B2D"
    dimension_meta = [
        ("valence", "愉悦度 V", "消极", "积极"),
        ("arousal", "唤醒度 A", "平静", "激动"),
        ("dominance", "控制感 D*", "弱 / 被控制", "强 / 有控制"),
    ]

    for row in range(len(data)):
        if row % 2 == 0:
            for ax in axes:
                ax.axhspan(row - 0.5, row + 0.5, color="#F5F7F7", zorder=0)

    for ax, (dim, title, low_label, high_label) in zip(axes[:3], dimension_meta):
        ax.axvline(0, color="#D6DADD", linewidth=1, zorder=1)
        for row, (_, item) in enumerate(data.iterrows()):
            nrc = item[f"{dim}_nrc"]
            elicited = item[f"{dim}_elicited_mean"]
            ax.plot([nrc, elicited], [row, row], color=connector_color, linewidth=3, solid_capstyle="round", zorder=2)
            ax.scatter(nrc, row, marker="s", s=70, color=lexical_color, edgecolor="white", linewidth=0.8, zorder=3)
            ax.scatter(elicited, row, marker="o", s=90, color=elicited_color, edgecolor="white", linewidth=0.8, zorder=4)
        ax.set_xlim(-1.05, 1.05)
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_ylim(len(data) - 0.5, -0.5)
        ax.set_title(title, fontsize=16, fontweight="bold", pad=18)
        ax.text(0.01, 1.01, f"← {low_label}", transform=ax.transAxes, color="#6D747A", fontsize=10, va="bottom")
        ax.text(0.99, 1.01, f"{high_label} →", transform=ax.transAxes, color="#6D747A", fontsize=10, va="bottom", ha="right")
        ax.tick_params(axis="y", length=0)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#AEB4B9")
        ax.grid(axis="x", color="#E6E9EB", linewidth=0.8, zorder=0)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(data["label"], fontsize=12)
    for ax in axes[1:3]:
        ax.set_yticks(y)
        ax.set_yticklabels([])

    ax = axes[3]
    ax.barh(y - 0.16, data["centroid_distance_vad"], height=0.28, color=raw_color, zorder=3)
    ax.barh(y + 0.16, data["calibrated_residual_vad"], height=0.28, color=calibrated_color, zorder=3)
    for row, item in data.iterrows():
        ax.text(item["centroid_distance_vad"] + 0.025, row - 0.16, f"{item['centroid_distance_vad']:.2f}", va="center", fontsize=9, color="#2F383D")
    ax.set_xlim(0, max(1.22, data["centroid_distance_vad"].max() + 0.16))
    ax.set_ylim(len(data) - 0.5, -0.5)
    ax.set_title("三维差异大小", fontsize=16, fontweight="bold", pad=18)
    ax.text(0.01, 1.01, "短 = 更重合", transform=ax.transAxes, color="#6D747A", fontsize=10, va="bottom")
    ax.set_yticks(y)
    ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#AEB4B9")
    ax.grid(axis="x", color="#E6E9EB", linewidth=0.8, zorder=0)

    fig.suptitle("同一个情绪词，实际诱发体验在哪里？", x=0.06, y=0.955, ha="left", fontsize=28, fontweight="bold", color="#20272B")
    fig.text(0.06, 0.895, "NRC 词义坐标与 DREAMER 影片诱发体验的 VAD 对照｜从上到下按原始三维距离递增", fontsize=14, color="#5D666C")

    legend_items = [
        Line2D([0], [0], marker="s", color="none", markerfacecolor=lexical_color, markeredgecolor="white", markersize=9, label="NRC 词义坐标"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=elicited_color, markeredgecolor="white", markersize=10, label="DREAMER 诱发体验"),
        Patch(facecolor=raw_color, label="绝对三维距离"),
        Patch(facecolor=calibrated_color, label="去除整体尺度差异后的残差"),
    ]
    fig.legend(handles=legend_items, loc="upper right", bbox_to_anchor=(0.97, 0.955), ncol=2, frameon=False, fontsize=11, handlelength=1.8, columnspacing=1.6)

    fig.text(0.06, 0.085, "读图：方块到圆点的连线越长，词义与真实体验在该维度上的差异越大。最右侧金色条用于区分情绪特异偏离与数据库整体量表压缩。", fontsize=11, color="#4F585E")
    fig.text(0.06, 0.048, "* Dominance 的原始 SAM 编码方向仍需结合实验界面核对；这里按 DREAMER 文件中的报告方向展示，不作心理机制解释。", fontsize=10, color="#8A4B45")

    for extension in ("png", "svg"):
        fig.savefig(
            RESULTS / f"DREAMER_NRC_直观对照图.{extension}",
            dpi=240 if extension == "png" else None,
            facecolor="white",
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
