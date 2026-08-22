"""Create the single main figure used in the two-page Japanese research brief."""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
INPUT = (
    ROOT
    / "public_data"
    / "dreamer_pilot"
    / "results"
    / "dreamer_trial_alignment_all_sensitivities.csv"
)
OUTPUT = ROOT / "results" / "dreamer_nrc_robustness"
OUTPUT_BASENAME = "figure_overview_main_readable"

DIMS = ("valence", "arousal", "dominance")
DIM_TITLES = {
    "valence": "感情価（Valence）",
    "arousal": "覚醒度（Arousal）",
    "dominance": "支配性（Dominance）",
}
EMOTION_LABELS = {
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
EMOTION_ORDER = (
    "happiness",
    "excitement",
    "anger",
    "calmness",
    "amusement",
    "fear",
    "surprise",
    "disgust",
    "sadness",
)
EMOTION_NUMBERS = {
    emotion: index for index, emotion in enumerate(EMOTION_ORDER, start=1)
}
MARKERS = {"valence": "o", "arousal": "s", "dominance": "^"}
NUMBER_OFFSETS = {
    "valence": {
        "happiness": (8, 9),
        "excitement": (-15, -2),
        "anger": (13, -2),
        "calmness": (-13, -13),
        "amusement": (-10, 15),
        "fear": (12, 9),
        "surprise": (11, -10),
        "disgust": (-10, 11),
        "sadness": (13, -11),
    },
    "arousal": {
        "happiness": (-30, -20),
        "excitement": (-32, 18),
        "anger": (30, -20),
        "calmness": (0, 15),
        "amusement": (10, -22),
        "fear": (15, 29),
        "surprise": (31, 10),
        "disgust": (-12, 30),
        "sadness": (0, 16),
    },
    "dominance": {
        "happiness": (16, 22),
        "excitement": (0, 26),
        "anger": (-17, 18),
        "calmness": (0, -17),
        "amusement": (17, -17),
        "fear": (15, 18),
        "surprise": (-18, -12),
        "disgust": (-10, 25),
        "sadness": (-16, 20),
    },
}


def main() -> None:
    raw = pd.read_csv(INPUT)
    data = raw[
        (raw["term_set"] == "noun")
        & (raw["dominance_orientation"] == "reported")
    ].copy()
    categories = (
        data.groupby("emotion", as_index=False)
        .agg(
            valence_nrc=("valence_nrc", "first"),
            arousal_nrc=("arousal_nrc", "first"),
            dominance_nrc=("dominance_nrc", "first"),
            valence_elicited=("valence_elicited", "mean"),
            arousal_elicited=("arousal_elicited", "mean"),
            dominance_elicited=("dominance_elicited", "mean"),
        )
        .sort_values("emotion")
    )
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Hiragino Sans",
                "Yu Gothic",
                "Noto Sans CJK JP",
                "Arial Unicode MS",
                "DejaVu Sans",
            ],
            "axes.unicode_minus": False,
            "font.size": 11,
            "axes.titlesize": 12.5,
            "axes.titleweight": "bold",
            "axes.labelsize": 11.5,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
        }
    )

    # A single horizontal row is required by the two-page format. Numbered
    # callouts replace repeated full labels so the points remain distinguishable
    # without making the figure taller or visually crowded.
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(12.0, 3.55),
        sharex=True,
        sharey=True,
    )

    for panel_index, (ax, dim) in enumerate(zip(axes, DIMS)):
        x = categories[f"{dim}_nrc"].to_numpy()
        y = categories[f"{dim}_elicited"].to_numpy()
        slope, intercept = np.polyfit(x, y, 1)
        grid = np.linspace(-1, 1, 100)

        ax.axline(
            (-1, -1),
            (1, 1),
            color="#A8A8A8",
            linewidth=1,
            linestyle="--",
            label="同一座標",
        )
        ax.plot(
            grid,
            intercept + slope * grid,
            color="#111111",
            linewidth=2,
            label="回帰直線",
        )
        ax.scatter(
            x,
            y,
            facecolor="#111111",
            marker=MARKERS[dim],
            edgecolor="white",
            linewidth=0.65,
            s=43,
            zorder=3,
        )
        for _, row in categories.iterrows():
            offset = NUMBER_OFFSETS[dim][row["emotion"]]
            ax.annotate(
                str(EMOTION_NUMBERS[row["emotion"]]),
                (row[f"{dim}_nrc"], row[f"{dim}_elicited"]),
                xytext=offset,
                textcoords="offset points",
                ha="center",
                va="center",
                fontsize=7.5,
                fontweight="bold",
                color="#111111",
                bbox={
                    "boxstyle": "circle,pad=0.18",
                    "facecolor": "white",
                    "edgecolor": "#4A4A4A",
                    "linewidth": 0.8,
                },
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#777777",
                    "linewidth": 0.7,
                    "shrinkA": 4,
                    "shrinkB": 3,
                },
                annotation_clip=False,
                zorder=4,
            )

        panel_letter = chr(ord("a") + panel_index)
        ax.set_title(f"（{panel_letter}）{DIM_TITLES[dim]}", pad=6)
        ax.set_xlim(-1.08, 1.08)
        ax.set_ylim(-1.08, 1.08)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax.axhline(0, color="#D7D7D7", linewidth=0.7, zorder=0)
        ax.axvline(0, color="#D7D7D7", linewidth=0.7, zorder=0)
        ax.grid(color="#E8E8E8", linewidth=0.55)

    fig.supxlabel(
        "感情語の意味的評価（NRC-VAD）",
        x=0.52,
        y=0.012,
        fontsize=11.5,
    )
    fig.supylabel(
        "映像後の情動体験評価（DREAMER）",
        x=0.018,
        y=0.52,
        fontsize=11.5,
    )
    legend_rows = (
        "1 幸福　2 興奮　3 怒り　4 平静　5 愉快　6 恐怖　7 驚き　8 嫌悪　9 悲しみ",
    )
    fig.text(
        0.53,
        0.105,
        "\n".join(legend_rows),
        ha="center",
        va="center",
        fontsize=9.6,
        linespacing=1.35,
    )
    fig.subplots_adjust(
        left=0.065,
        right=0.995,
        bottom=0.22,
        top=0.89,
        wspace=0.20,
    )
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(
            OUTPUT / f"{OUTPUT_BASENAME}.{extension}",
            dpi=260 if extension == "png" else None,
            bbox_inches="tight",
            facecolor="white",
        )
    plt.close(fig)


if __name__ == "__main__":
    main()
