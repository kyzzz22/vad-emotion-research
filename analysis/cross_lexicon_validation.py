"""Cross-lexicon validation: NRC-VAD v2 vs Warriner (2013) as lexical VAD references.

Compares the 9 DREAMER emotion categories' elicited VAD against two independent
lexical norms to test whether the choice of lexicon drives the conclusions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "cross_lexicon"
RESULTS.mkdir(parents=True, exist_ok=True)

DREAMER_CATEGORIES = ROOT / "public_data" / "dreamer_pilot" / "results"
WARRINER_PATH = ROOT / "public_data" / "Ratings_Warriner_et_al.csv"
NRC_PATH = ROOT / "public_data" / "case_pilot" / "nrc_vad"

SEED = 20260724
rng = np.random.default_rng(SEED)

# ── Word mappings ──────────────────────────────────────────────────────────
NOUN_TERMS = {
    "happiness": "happiness", "excitement": "excitement", "anger": "anger",
    "calmness": "calmness",   "amusement": "amusement",   "fear": "fear",
    "surprise": "surprise",   "disgust": "disgust",       "sadness": "sadness",
}
ADJECTIVE_TERMS = {
    "happiness": "happy",   "excitement": "excited", "anger": "angry",
    "calmness": "calm",     "amusement": "amused",   "fear": "afraid",
    "surprise": "surprised","disgust": "disgusted",  "sadness": "sad",
}

DIMS = ("valence", "arousal", "dominance")

# ── Warriner loading ────────────────────────────────────────────────────────
def load_warriner(path: Path) -> pd.DataFrame:
    w = pd.read_csv(path)
    w = w.rename(columns={
        "V.Mean.Sum": "valence", "A.Mean.Sum": "arousal", "D.Mean.Sum": "dominance",
    })
    w["Word_lower"] = w["Word"].str.lower().str.strip()
    return w.set_index("Word_lower")

def lookup_warriner(warriner: pd.DataFrame, word: str) -> dict[str, float]:
    key = word.lower().strip()
    if key in warriner.index:
        row = warriner.loc[key]
        return {dim: float(row[dim]) for dim in DIMS}
    return {}

def map_to_warriner(warriner: pd.DataFrame, term_map: dict[str, str]) -> pd.DataFrame:
    rows = []
    for emotion, word in term_map.items():
        coords = lookup_warriner(warriner, word)
        coords["emotion"] = emotion
        coords["word"] = word
        rows.append(coords)
    return pd.DataFrame(rows).set_index("emotion")

# ── NRC loading (from frozen DREAMER summary) ──────────────────────────────
def load_dreamer_nrc() -> pd.DataFrame:
    """Load NRC-VAD coordinates frozen in DREAMER category summary."""
    summary = pd.read_csv(DREAMER_CATEGORIES / "dreamer_category_summary.csv")
    noun = summary[(summary["term_set"] == "noun") & (summary["dominance_orientation"] == "reported")]
    nrc = noun[["emotion", "valence_nrc", "arousal_nrc", "dominance_nrc"]].drop_duplicates()
    nrc = nrc.rename(columns={f"{d}_nrc": d for d in DIMS})
    nrc = nrc.set_index("emotion")
    # NRC is in [-1, 1]; transform to 1-9 for direct comparison with Warriner
    nrc_1to9 = nrc.copy()
    for d in DIMS:
        nrc_1to9[f"{d}_raw"] = nrc[d]  # keep original
        nrc_1to9[d] = nrc[d] * 4 + 5   # [-1,1] → [1,9]
    return nrc_1to9

# ── Main analysis ───────────────────────────────────────────────────────────
def main() -> None:
    # Load Warriner
    warriner = load_warriner(WARRINER_PATH)
    print(f"Loaded Warriner: {len(warriner)} words")

    # Map 9 emotions × 2 word forms to Warriner
    noun_w = map_to_warriner(warriner, NOUN_TERMS)
    adj_w = map_to_warriner(warriner, ADJECTIVE_TERMS)
    print("Warriner noun mapping:")
    print(noun_w)
    print("\nWarriner adjective mapping:")
    print(adj_w)

    # Load NRC (transformed to 1-9)
    nrc = load_dreamer_nrc()
    print("\nNRC-VAD (1-9 scale):")
    print(nrc[["valence", "arousal", "dominance"]])

    # Load DREAMER elicited (1-9 scale from raw 1-5 scores)
    summary = pd.read_csv(DREAMER_CATEGORIES / "dreamer_category_summary.csv")
    elicited = summary[
        (summary["term_set"] == "noun") & (summary["dominance_orientation"] == "reported")
    ].set_index("emotion")
    # Convert elicited back to 1-9: elicited is in [-1,1], score = elicited*2+3
    deap_scale = pd.DataFrame(index=elicited.index)
    for d in DIMS:
        deap_scale[d] = elicited[f"{d}_elicited_mean"] * 2 + 3

    print("\nDREAMER elicited (1-9 scale):")
    print(deap_scale.round(2))

    # ── Compute correlations ─────────────────────────────────────────────
    emotions = list(NOUN_TERMS.keys())
    rows = []
    for dim in DIMS:
        for lexicon_name, lexicon_df in [("NRC-VAD", nrc), ("Warriner-noun", noun_w), ("Warriner-adj", adj_w)]:
            lex_vals = np.array([lexicon_df.loc[e, dim] for e in emotions])
            eli_vals = np.array([deap_scale.loc[e, dim] for e in emotions])
            mask = ~(np.isnan(lex_vals) | np.isnan(eli_vals))
            if mask.sum() < 4:
                continue
            r, p_pearson = stats.pearsonr(lex_vals[mask], eli_vals[mask])
            rho, p_spearman = stats.spearmanr(lex_vals[mask], eli_vals[mask])
            rows.append({
                "lexicon": lexicon_name, "dimension": dim, "n": int(mask.sum()),
                "pearson_r": round(r, 4), "pearson_p": round(p_pearson, 4),
                "spearman_rho": round(rho, 4), "spearman_p": round(p_spearman, 4),
            })

    corr_df = pd.DataFrame(rows)
    print("\n=== Cross-Lexicon Correlations (NRC vs Warriner) ===")
    print(corr_df.to_string(index=False))
    corr_df.to_csv(RESULTS / "cross_lexicon_correlations.csv", index=False)

    # ── Figure: side-by-side comparison ───────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), facecolor="white")
    dim_labels = {"valence": "Valence", "arousal": "Arousal", "dominance": "Dominance"}
    colors = {"NRC-VAD": "#5E6670", "Warriner-noun": "#D6862D", "Warriner-adj": "#A45D1B"}
    markers = {"NRC-VAD": "s", "Warriner-noun": "o", "Warriner-adj": "^"}

    for ax_idx, dim in enumerate(DIMS):
        ax = axes[ax_idx]
        for lex_name, lex_df in [("NRC-VAD", nrc), ("Warriner-noun", noun_w), ("Warriner-adj", adj_w)]:
            lex_vals = np.array([lex_df.loc[e, dim] for e in emotions])
            eli_vals = np.array([deap_scale.loc[e, dim] for e in emotions])
            c = colors[lex_name]
            ax.scatter(lex_vals, eli_vals, c=c, marker=markers[lex_name],
                       s=80, edgecolors="white", linewidth=0.8, zorder=3,
                       label=lex_name)
            # Regression line
            mask = ~(np.isnan(lex_vals) | np.isnan(eli_vals))
            if mask.sum() >= 4:
                slope, intercept = np.polyfit(lex_vals[mask], eli_vals[mask], 1)
                x_line = np.linspace(lex_vals[mask].min() - 0.5, lex_vals[mask].max() + 0.5, 50)
                ax.plot(x_line, slope * x_line + intercept, color=c, linewidth=1.2,
                        linestyle="--", alpha=0.7)

        # Identity line
        lims = [0, 10]
        ax.plot(lims, lims, color="#D0D5D9", linewidth=0.8, linestyle=":", zorder=1)
        ax.set_xlim(0.5, 9.5)
        ax.set_ylim(0.5, 9.5)
        ax.set_xlabel(f"Lexical {dim_labels[dim]} (1–9)", fontsize=11, color="#2D3339")
        ax.set_ylabel(f"DREAMER Elicited {dim_labels[dim]} (1–9)", fontsize=11, color="#2D3339")
        ax.set_title(dim_labels[dim], fontsize=13, fontweight="bold", color="#20272B")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.25, color="#BAC1C7")

    axes[1].legend(frameon=False, fontsize=9, loc="lower right",
                   handletextpad=0.5, labelspacing=0.4)
    fig.suptitle("Cross-Lexicon Validation: NRC-VAD vs Warriner (2013) as Lexical VAD Reference",
                 fontsize=14, fontweight="bold", color="#20272B", y=1.01)
    fig.tight_layout()
    fig.savefig(RESULTS / "cross_lexicon_comparison.png", dpi=200, facecolor="white",
                bbox_inches="tight")
    fig.savefig(RESULTS / "cross_lexicon_comparison.svg", facecolor="white",
                bbox_inches="tight")
    plt.close(fig)
    print(f"\nFigure saved to {RESULTS / 'cross_lexicon_comparison.png'}")

    # ── Summary table ─────────────────────────────────────────────────────
    print("\n=== Summary: Dimension-specific pattern consistency ===")
    for dim in DIMS:
        nrc_row = corr_df[(corr_df["lexicon"] == "NRC-VAD") & (corr_df["dimension"] == dim)]
        w_row = corr_df[(corr_df["lexicon"] == "Warriner-noun") & (corr_df["dimension"] == dim)]
        if len(nrc_row) and len(w_row):
            print(f"{dim:10s}: NRC r={nrc_row.iloc[0]['pearson_r']:.3f}, "
                  f"Warriner r={w_row.iloc[0]['pearson_r']:.3f}, "
                  f"Δr={w_row.iloc[0]['pearson_r'] - nrc_row.iloc[0]['pearson_r']:+.3f}")

    # Save manifest
    manifest = {
        "analysis": "Cross-lexicon validation: NRC-VAD v2 vs Warriner (2013)",
        "databases": ["NRC-VAD v2.1", "Warriner et al. (2013)", "DREAMER v1.0.2"],
        "emotions": 9,
        "lexicons_compared": 3,
        "random_seed": SEED,
    }
    with open(RESULTS / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
