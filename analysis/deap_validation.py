"""DEAP independent replication: validate DREAMER findings on a different database.

DEAP: 32 participants × 40 music videos, V+A+D+Liking (1-9 SAM), 32ch EEG.
Compares DEAP elicited VAD against Warriner (2013) and NRC-VAD lexical norms,
providing an independent cross-database replication of the DREAMER results.
"""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "deap_validation"
RESULTS.mkdir(parents=True, exist_ok=True)

DEAP_DIR = ROOT / "public_data" / "licensed" / "deap" / "deap-dataset"
DATA_DIR = DEAP_DIR / "data_preprocessed_python"
META_DIR = DEAP_DIR / "metadata_xls"
WARRINER_PATH = ROOT / "public_data" / "Ratings_Warriner_et_al.csv"
DREAMER_SUMMARY = ROOT / "public_data" / "dreamer_pilot" / "results" / "dreamer_category_summary.csv"

SEED = 20260724
N_BOOTSTRAP = 3000
rng = np.random.default_rng(SEED)

DIMS = ("valence", "arousal", "dominance")

# ── Data loading ────────────────────────────────────────────────────────────
def load_deap_labels() -> pd.DataFrame:
    """Load VAD labels from all 32 DEAP participants."""
    rows = []
    for pid in range(1, 33):
        path = DATA_DIR / f"s{pid:02d}.dat"
        with open(path, "rb") as f:
            subj = pickle.load(f, encoding="latin1")
        for trial in range(40):
            rows.append({
                "participant": pid,
                "trial": trial + 1,
                "valence": float(subj["labels"][trial, 0]),
                "arousal": float(subj["labels"][trial, 1]),
                "dominance": float(subj["labels"][trial, 2]),
                "liking": float(subj["labels"][trial, 3]),
            })
    return pd.DataFrame(rows)

def load_video_tags() -> pd.DataFrame:
    """Load DEAP video metadata with Last.fm tags."""
    videos = pd.read_excel(META_DIR / "video_list.xls")
    # Map melancholic → melancholy for Warriner lookup
    videos["Lastfm_tag"] = videos["Lastfm_tag"].fillna("").str.strip().str.lower()
    videos.loc[videos["Lastfm_tag"] == "melancholic", "Lastfm_tag"] = "melancholy"
    return videos[["Experiment_id", "Lastfm_tag", "Artist", "Title"]].copy()

def load_warriner() -> pd.DataFrame:
    """Load Warriner norms indexed by lowercase word."""
    w = pd.read_csv(WARRINER_PATH)
    w = w.rename(columns={
        "V.Mean.Sum": "valence", "A.Mean.Sum": "arousal", "D.Mean.Sum": "dominance",
    })
    w["word_lower"] = w["Word"].str.lower().str.strip()
    return w.set_index("word_lower")

def load_nrc_lexicon() -> pd.DataFrame:
    """Load NRC-VAD v2.1 from local path (gitignored)."""
    candidates = [
        ROOT / "public_data" / "nrc_vad" / "NRC-VAD-Lexicon-v2.1.txt",
        ROOT / "public_data" / "case_pilot" / "nrc_vad" / "NRC-VAD-Lexicon-v2.1.txt",
    ]
    for p in candidates:
        if p.exists():
            nrc = pd.read_csv(p, sep="\t")
            # NRC-VAD v2 uses "term" as word column; also handle "Word" in other versions
            word_col = "term" if "term" in nrc.columns else "Word"
            nrc["Word_lower"] = nrc[word_col].str.lower().str.strip()
            return nrc.set_index("Word_lower")
    print("WARNING: NRC-VAD lexicon not found, using Warriner only", file=sys.stderr)
    return None

# ── Scale transforms ────────────────────────────────────────────────────────
def warriner_to_normed(warriner_df: pd.DataFrame) -> pd.DataFrame:
    """Transform Warriner 1-9 to [-1, 1]."""
    out = warriner_df.copy()
    for d in DIMS:
        out[d] = (out[d] - 5.0) / 4.0
    return out

def deap_to_normed(deap_df: pd.DataFrame) -> pd.DataFrame:
    """Transform DEAP 1-9 to [-1, 1]."""
    out = deap_df.copy()
    for d in DIMS:
        out[d] = (out[d] - 5.0) / 4.0
    return out

# ── Bootstrap ───────────────────────────────────────────────────────────────
def hierarchical_bootstrap(labels: pd.DataFrame, n_iter: int, rng: np.random.Generator):
    """Two-level bootstrap: resample participants + videos."""
    participants = sorted(labels["participant"].unique())
    videos = sorted(labels["trial"].unique())
    n_p = len(participants)
    n_v = len(videos)

    # Build a lookup: trial → lexical VAD (already merged into labels)
    tag_lookup = labels[["trial", "tag", "w_valence", "w_arousal", "w_dominance",
                          "nrc_valence", "nrc_arousal", "nrc_dominance"]].drop_duplicates()
    tag_lookup = tag_lookup.set_index("trial")

    corr_records = []
    slope_records = []

    for _ in range(n_iter):
        p_sample = rng.choice(participants, size=n_p, replace=True)
        v_sample = rng.choice(videos, size=n_v, replace=True)

        boot_data = labels[
            labels["participant"].isin(p_sample) & labels["trial"].isin(v_sample)
        ]
        # Per-video mean of elicited VAD
        means = boot_data.groupby("trial")[["valence", "arousal", "dominance"]].mean()
        # Attach lexical VAD from lookup
        for col in ["tag", "w_valence", "w_arousal", "w_dominance",
                     "nrc_valence", "nrc_arousal", "nrc_dominance"]:
            means[col] = means.index.map(tag_lookup[col])

        for lexicon_name, lex_prefix in [("Warriner", "w_"), ("NRC", "nrc_")]:
            valid = means.dropna(subset=[f"{lex_prefix}valence"])
            if len(valid) < 5:
                continue

            for dim in DIMS:
                lex = valid[f"{lex_prefix}{dim}"].values
                eli = valid[dim].values
                r_val, _ = stats.pearsonr(lex, eli)
                rho_val, _ = stats.spearmanr(lex, eli)

                # Affine slope
                slope, _ = np.polyfit(lex, eli, 1)

                corr_records.append({
                    "lexicon": lexicon_name, "dimension": dim,
                    "pearson_r": r_val, "spearman_rho": rho_val,
                })
                slope_records.append({
                    "lexicon": lexicon_name, "dimension": dim,
                    "slope": slope,
                })

    corr_ci = pd.DataFrame(corr_records).groupby(["lexicon", "dimension"]).quantile([0.025, 0.5, 0.975])
    slope_ci = pd.DataFrame(slope_records).groupby(["lexicon", "dimension"]).quantile([0.025, 0.5, 0.975])
    return corr_ci, slope_ci

# ── Figures ─────────────────────────────────────────────────────────────────
def make_figures(means, deap_agg, dreamer_ref, corr_summary, slope_summary):
    """Generate DEAP validation figures."""
    # Figure 1: DEAP scatter + DREAMER overlay
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), facecolor="white")

    dim_full = {"valence": "Valence", "arousal": "Arousal", "dominance": "Dominance"}
    nrc_colors = {"valence": "#B44B45", "arousal": "#177F73", "dominance": "#386EA0"}

    # DEAP tags as points
    for ax_i, dim in enumerate(DIMS):
        ax = axes[ax_i]
        w_vals = means[f"w_{dim}"].values
        d_vals = means[dim].values
        mask = ~(np.isnan(w_vals) | np.isnan(d_vals))
        ax.scatter(w_vals[mask], d_vals[mask], c="#D6862D", s=50, alpha=0.7,
                   edgecolors="white", linewidth=0.5, zorder=3, label=f"DEAP (n={mask.sum()})")

        # DEAP regression line
        if mask.sum() >= 5:
            slope, intercept = np.polyfit(w_vals[mask], d_vals[mask], 1)
            xl = np.linspace(w_vals[mask].min() - 0.15, w_vals[mask].max() + 0.15, 50)
            ax.plot(xl, slope * xl + intercept, color="#D6862D", linewidth=1.5,
                    linestyle="--", alpha=0.8)

        # DREAMER 9-point overlay (from Warriner reference)
        dreamer_w = dreamer_ref[f"w_{dim}"].values
        dreamer_e = dreamer_ref[dim].values
        ax.scatter(dreamer_w, dreamer_e, c="#5E6670", s=100, marker="D",
                   edgecolors="white", linewidth=0.8, zorder=4, label="DREAMER (9 categories)")

        # Identity
        lo, hi = -1.15, 1.15
        ax.plot([lo, hi], [lo, hi], color="#D0D5D9", linewidth=0.8, linestyle=":", zorder=1)
        ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
        ax.set_xlabel(f"Warriner Lexical {dim_full[dim]}", fontsize=11, color="#3D4349")
        ax.set_ylabel(f"DEAP Elicited {dim_full[dim]}", fontsize=11, color="#3D4349")
        ax.set_title(dim_full[dim], fontsize=13, fontweight="bold", color="#20272B")

        # Annotate with correlation
        row = corr_summary[(corr_summary["lexicon"] == "Warriner") & (corr_summary["dimension"] == dim)]
        if len(row) > 0:
            r_val = row.iloc[0]["pearson_r"]
            ax.text(0.05, 0.93, f"r = {r_val:.3f}", transform=ax.transAxes,
                    fontsize=10, color="#3D4349", va="top")

        ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.grid(True, alpha=0.2, color="#BAC1C7")
        if ax_i == 1:
            ax.legend(frameon=False, fontsize=8.5, loc="lower right")

    fig.suptitle("DEAP (32 participants × 40 music videos) vs Warriner Lexical VAD — with DREAMER Overlay",
                 fontsize=13, fontweight="bold", color="#20272B", y=1.01)
    fig.tight_layout()
    fig.savefig(RESULTS / "deap_scatter_with_dreamer.png", dpi=200, facecolor="white",
                bbox_inches="tight")
    fig.savefig(RESULTS / "deap_scatter_with_dreamer.svg", facecolor="white",
                bbox_inches="tight")
    plt.close(fig)

    # Figure 2: DREAMER vs DEAP slope comparison
    fig2, ax2 = plt.subplots(figsize=(8, 4.5), facecolor="white")
    x = np.arange(3)
    width = 0.3

    # DREAMER slopes from original analysis
    dreamer_slope_vals = [0.520, 0.341, -0.055]  # V, A, D

    # DEAP slopes (Warriner-based) with bootstrap CIs
    deap_slope_vals = []
    deap_err_lo = []
    deap_err_hi = []
    for d in DIMS:
        if ("Warriner", d) in slope_summary.index:
            ci_group = slope_summary.loc[("Warriner", d)]
            med = ci_group.iloc[1]["slope"]  # 50th percentile
            lo = ci_group.iloc[0]["slope"]   # 2.5th
            hi = ci_group.iloc[2]["slope"]   # 97.5th
            deap_slope_vals.append(med)
            deap_err_lo.append(med - lo)
            deap_err_hi.append(hi - med)
        else:
            deap_slope_vals.append(0)
            deap_err_lo.append(0)
            deap_err_hi.append(0)

    deap_err = [deap_err_lo, deap_err_hi]

    bars1 = ax2.bar(x - width/2, dreamer_slope_vals, width, color="#5E6670",
                    label="DREAMER (9 film categories, N=23)", zorder=3)
    bars2 = ax2.bar(x + width/2, deap_slope_vals, width, color="#D6862D",
                    yerr=deap_err, capsize=5, label="DEAP (40 music videos, N=32)", zorder=3)

    ax2.axhline(y=1.0, color="#D0D5D9", linewidth=0.8, linestyle="--")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["Valence", "Arousal", "Dominance"], fontsize=12)
    ax2.set_ylabel("Lexical → Elicited Slope", fontsize=11, color="#3D4349")
    ax2.set_title("Scale Compression: DREAMER vs DEAP", fontsize=13, fontweight="bold", color="#20272B")
    ax2.legend(frameon=False, fontsize=9)
    ax2.spines["top"].set_visible(False); ax2.spines["right"].set_visible(False)
    ax2.grid(True, alpha=0.2, color="#BAC1C7", axis="y")
    ax2.set_ylim(-0.3, 1.4)
    fig2.tight_layout()
    fig2.savefig(RESULTS / "deap_dreamer_slope_comparison.png", dpi=200, facecolor="white",
                 bbox_inches="tight")
    fig2.savefig(RESULTS / "deap_dreamer_slope_comparison.svg", facecolor="white",
                 bbox_inches="tight")
    plt.close(fig2)


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("DEAP Independent Replication Analysis")
    print("=" * 60)

    # 1. Load DEAP labels
    labels = load_deap_labels()
    print(f"Loaded DEAP: {labels['participant'].nunique()} participants × "
          f"{labels['trial'].nunique()} trials = {len(labels)} observations")

    # 2. Load video tags
    tags = load_video_tags()
    labels = labels.merge(tags, left_on="trial", right_index=True, how="left")
    labels["tag"] = labels["Lastfm_tag"]
    unique_tags = sorted(labels["tag"].dropna().unique())
    print(f"Unique video tags: {len(unique_tags)}")

    # 3. Map tags to Warriner VAD
    warriner = load_warriner()
    w_coords = {}
    missing = []
    for tag in unique_tags:
        if tag in warriner.index:
            w_coords[tag] = {d: float(warriner.loc[tag, d]) for d in DIMS}
        else:
            missing.append(tag)
    if missing:
        print(f"WARNING: {len(missing)} tags missing from Warriner: {missing}")

    # Add Warriner VAD to each trial
    for d in DIMS:
        labels[f"w_{d}"] = labels["tag"].map(lambda t: w_coords.get(t, {}).get(d, np.nan))
    print(f"Warriner mapping: {len(w_coords)}/{len(unique_tags)} tags mapped")

    # 4. Map tags to NRC-VAD (if available)
    nrc = load_nrc_lexicon()
    has_nrc = nrc is not None
    if has_nrc:
        nrc_coords = {}
        nrc_missing = []
        for tag in unique_tags:
            if tag in nrc.index:
                nrc_coords[tag] = {d: float(nrc.loc[tag, d]) for d in DIMS}
            else:
                nrc_missing.append(tag)
        for d in DIMS:
            labels[f"nrc_{d}"] = labels["tag"].map(lambda t: nrc_coords.get(t, {}).get(d, np.nan))
        print(f"NRC-VAD mapping: {len(nrc_coords)}/{len(unique_tags)} tags mapped")
    else:
        for d in DIMS:
            labels[f"nrc_{d}"] = np.nan
        print("NRC-VAD: not available, skipping")

    # 5. Per-video aggregate
    means = labels.groupby(["trial", "tag"], as_index=False).agg(
        valence=("valence", "mean"), valence_sd=("valence", "std"),
        arousal=("arousal", "mean"), arousal_sd=("arousal", "std"),
        dominance=("dominance", "mean"), dominance_sd=("dominance", "std"),
        liking=("liking", "mean"),
        w_valence=("w_valence", "first"), w_arousal=("w_arousal", "first"),
        w_dominance=("w_dominance", "first"),
        nrc_valence=("nrc_valence", "first"), nrc_arousal=("nrc_arousal", "first"),
        nrc_dominance=("nrc_dominance", "first"),
    )
    print(f"\nPer-video means: {len(means)} videos")
    means.to_csv(RESULTS / "deap_video_summary.csv", index=False, float_format="%.4f")

    # 6. Correlations (point estimate on full data)
    corr_rows = []
    for lexicon_name, prefix in [("Warriner", "w_"), ("NRC", "nrc_")]:
        for dim in DIMS:
            lex_col = f"{prefix}{dim}"
            valid = means[[dim, lex_col]].dropna()
            if len(valid) < 5:
                continue
            r, p_pearson = stats.pearsonr(valid[lex_col], valid[dim])
            rho, p_spearman = stats.spearmanr(valid[lex_col], valid[dim])
            corr_rows.append({
                "lexicon": lexicon_name, "dimension": dim, "n": len(valid),
                "pearson_r": round(r, 4), "pearson_p": round(p_pearson, 4),
                "spearman_rho": round(rho, 4), "spearman_p": round(p_spearman, 4),
            })

    corr_summary = pd.DataFrame(corr_rows)
    print("\n=== DEAP × Lexical VAD Correlations ===")
    print(corr_summary.to_string(index=False))
    corr_summary.to_csv(RESULTS / "deap_correlations.csv", index=False)

    # 7. Affine slopes (point estimate)
    slope_rows = []
    for lexicon_name, prefix in [("Warriner", "w_"), ("NRC", "nrc_")]:
        for dim in DIMS:
            lex_col = f"{prefix}{dim}"
            valid = means[[dim, lex_col]].dropna()
            if len(valid) < 5:
                continue
            slope, intercept = np.polyfit(valid[lex_col], valid[dim], 1)
            slope_rows.append({
                "lexicon": lexicon_name, "dimension": dim,
                "slope": round(slope, 4), "intercept": round(intercept, 4),
            })

    slope_df = pd.DataFrame(slope_rows)
    print("\n=== Affine Mapping (Lexical → DEAP) ===")
    print(slope_df.to_string(index=False))
    slope_df.to_csv(RESULTS / "deap_affine_mapping.csv", index=False)

    # 8. Hierarchical bootstrap
    print(f"\nRunning hierarchical bootstrap ({N_BOOTSTRAP} iterations)...")
    corr_ci, slope_ci = hierarchical_bootstrap(labels, N_BOOTSTRAP, rng)

    print("\n=== Bootstrap Correlation CIs ===")
    for lex_name in ["Warriner", "NRC"]:
        if (lex_name, "valence") not in corr_ci.index:
            continue
        for dim in DIMS:
            ci_lo = corr_ci.loc[(lex_name, dim)].iloc[0]["pearson_r"]
            ci_med = corr_ci.loc[(lex_name, dim)].iloc[1]["pearson_r"]
            ci_hi = corr_ci.loc[(lex_name, dim)].iloc[2]["pearson_r"]
            print(f"  {lex_name:10s} {dim:10s}: r={ci_med:.3f} [{ci_lo:.3f}, {ci_hi:.3f}]")

    corr_ci.reset_index().to_csv(RESULTS / "deap_bootstrap_correlations.csv", index=False)
    slope_ci.reset_index().to_csv(RESULTS / "deap_bootstrap_slopes.csv", index=False)

    # 9. Prepare DREAMER reference for overlay
    # Load DREAMER summary and transform to Warriner normed [-1,1]
    dreamer_sum = pd.read_csv(DREAMER_SUMMARY)
    dreamer_noun = dreamer_sum[
        (dreamer_sum["term_set"] == "noun") & (dreamer_sum["dominance_orientation"] == "reported")
    ].copy()
    # DREAMER elicited is already [-1,1], NRC is [-1,1]
    # Map DREAMER emotions to Warriner for reference
    dreamer_w_mapping = {
        "happiness": "happiness", "excitement": "excitement", "anger": "anger",
        "calmness": "calmness", "amusement": "amusement", "fear": "fear",
        "surprise": "surprise", "disgust": "disgust", "sadness": "sadness",
    }
    dreamer_ref = pd.DataFrame(index=dreamer_noun["emotion"])
    dreamer_ref["valence"] = dreamer_noun["valence_elicited_mean"].values
    dreamer_ref["arousal"] = dreamer_noun["arousal_elicited_mean"].values
    dreamer_ref["dominance"] = dreamer_noun["dominance_elicited_mean"].values
    for d in DIMS:
        dreamer_ref[f"w_{d}"] = dreamer_ref.index.map(
            lambda e: (w_coords.get(dreamer_w_mapping.get(e, ""), {}).get(d, np.nan) or np.nan))
    # Warriner 1-9 → [-1,1]
    for d in DIMS:
        dreamer_ref[f"w_{d}"] = (dreamer_ref[f"w_{d}"] - 5.0) / 4.0

    # DREAMER slopes from original analysis (affine_scale_mapping.csv)
    # These are slopes of NRC→DREAMER, NRC in [-1,1], DREAMER in [-1,1]
    dreamer_slope_ref = {
        "valence": 0.520, "arousal": 0.341, "dominance": -0.055,
    }

    # 10. Generate figures (Warriner-based)
    # First convert means to normed [-1,1] for plotting
    means_normed = means.copy()
    for d in DIMS:
        means_normed[d] = (means_normed[d] - 5.0) / 4.0   # DEAP 1-9 → [-1,1]
        means_normed[f"w_{d}"] = (means_normed[f"w_{d}"] - 5.0) / 4.0  # Warriner 1-9 → [-1,1]

    make_figures(means_normed, means, dreamer_ref, corr_summary, slope_ci)

    # ── Cross-database summary ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CROSS-DATABASE COMPARISON")
    print("=" * 60)
    print(f"{'Dimension':<12} {'DREAMER r':>10} {'DEAP r':>10} {'DREAMER slope':>14} {'DEAP slope':>12}")
    for i, dim in enumerate(DIMS):
        dreamer_r = dreamer_slope_ref[dim]  # placeholder — use actual data
        deap_row = corr_summary[(corr_summary["lexicon"] == "Warriner") & (corr_summary["dimension"] == dim)]
        deap_r = deap_row.iloc[0]["pearson_r"] if len(deap_row) > 0 else np.nan
        deap_s = slope_df[(slope_df["lexicon"] == "Warriner") & (slope_df["dimension"] == dim)]
        deap_slope = deap_s.iloc[0]["slope"] if len(deap_s) > 0 else np.nan
        # Get DREAMER r from the cross-lexicon analysis
        dreamer_actual_r = {"valence": 0.875, "arousal": 0.832, "dominance": -0.121}[dim]
        print(f"{dim:<12} {dreamer_actual_r:>10.3f} {deap_r:>10.3f} {dreamer_slope_ref[dim]:>14.3f} {deap_slope:>12.3f}")

    # Save manifest
    manifest = {
        "analysis": "DEAP independent replication of DREAMER VAD alignment findings",
        "database": "DEAP (Koelstra et al., 2012)",
        "participants": 32,
        "videos": 40,
        "trials": 1280,
        "lexical_reference": "Warriner et al. (2013)",
        "bootstrap_iterations": N_BOOTSTRAP,
        "random_seed": SEED,
        "scale_transform": "(score - 5) / 4 for both DEAP and Warriner (1-9 → [-1,1])",
    }
    with open(RESULTS / "run_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nAll outputs saved to {RESULTS}")

if __name__ == "__main__":
    main()
