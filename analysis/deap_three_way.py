"""DEAP three-way decomposition: lexical, stimulus-judgment, and felt-experience VAD.

DEAP provides TWO independent VAD ratings for the same 40 music videos:
  (A) Online VAD — ratings by independent judges (stimulus emotional content)
  (B) Lab VAD   — 32 participants' self-reported felt experience

Combined with lexical VAD (17/40 videos have valid Warriner tags via Experiment_id),
this allows isolating WHERE the alignment breaks via three independent comparisons:

  1. Lexical → Stimulus: Do word-tags carry valid emotional info?  (n=17)
  2. Stimulus → Experience: Does stimulus judgment predict felt experience? (n=40)
  3. Lexical → Experience: Direct transportability test. (n=17)

Column naming: x=leXical, o=Online, l=Lab; v=valence, a=arousal, d=dominance.
All values in [-1,+1] via (X-5)/4 from original 1-9 scale.
"""

from __future__ import annotations

import json, pickle, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "deap_three_way"
RESULTS.mkdir(parents=True, exist_ok=True)
DEAP_DIR = ROOT / "public_data" / "licensed" / "deap" / "deap-dataset"
WARRINER_PATH = ROOT / "public_data" / "Ratings_Warriner_et_al.csv"

SEED, N_BOOT = 20260730, 5000
rng = np.random.default_rng(SEED)

# DIM_CODES maps: 1-char column suffix → full dimension name
DIM_MAP = {"v": "valence", "a": "arousal", "d": "dominance"}
DIM_FULL = {"v": "Valence", "a": "Arousal", "d": "Dominance"}
DIM_SHORT = {"v": "Valence", "a": "Arousal", "d": "Dominance"}
DIM_COLORS = {"v": "#B44B45", "a": "#177F73", "d": "#386EA0"}

# ── Data loading ──────────────────────────────────────────────────────────
def load_all() -> pd.DataFrame:
    pr = pd.read_excel(DEAP_DIR / "metadata_xls" / "participant_ratings.xls")
    vl = pd.read_excel(DEAP_DIR / "metadata_xls" / "video_list.xls")
    w = pd.read_csv(WARRINER_PATH)
    w = w.rename(columns={"V.Mean.Sum": "wv", "A.Mean.Sum": "wa", "D.Mean.Sum": "wd"})
    w["wl"] = w["Word"].str.lower().str.strip()
    w = w.set_index("wl")

    # Build Experiment_id → video_list lookup (EIDs 1-40)
    vl_eid = vl[vl["Experiment_id"].notna()].copy()
    vl_eid["eid"] = vl_eid["Experiment_id"].astype(int)
    vl_eid = vl_eid[vl_eid["eid"].between(1, 40)].set_index("eid")

    # Lab VAD means: trial index in .dat = Experiment_id - 1
    rows = []
    for pid in range(1, 33):
        with open(DEAP_DIR / "data_preprocessed_python" / f"s{pid:02d}.dat", "rb") as f:
            subj = pickle.load(f, encoding="latin1")
        for t in range(40):
            rows.append({"participant": pid, "eid": t + 1,
                         "lv_raw": float(subj["labels"][t, 0]),
                         "la_raw": float(subj["labels"][t, 1]),
                         "ld_raw": float(subj["labels"][t, 2])})
    lab = pd.DataFrame(rows)
    df = lab.groupby("eid").agg(
        lv_raw=("lv_raw", "mean"), la_raw=("la_raw", "mean"), ld_raw=("ld_raw", "mean")
    ).reset_index()

    # Merge Online VAD from video_list
    for col, vcol in [("ov_raw", "AVG_Valence"), ("oa_raw", "AVG_Arousal"), ("od_raw", "AVG_Dominance")]:
        df[col] = df["eid"].map(lambda e: float(vl_eid.loc[e, vcol]) if e in vl_eid.index else np.nan)

    # Merge tags → Warriner lexical VAD
    df["tag"] = df["eid"].map(lambda e: str(vl_eid.loc[e, "Lastfm_tag"]).strip().lower()
                               if e in vl_eid.index and pd.notna(vl_eid.loc[e, "Lastfm_tag"]) else "")
    df.loc[df["tag"].isin(["nan", ""]), "tag"] = ""
    df.loc[df["tag"] == "melancholic", "tag"] = "melancholy"

    for d_code, w_col in [("v", "wv"), ("a", "wa"), ("d", "wd")]:
        df[f"x{d_code}_raw"] = df["tag"].apply(
            lambda t: float(w.loc[t, w_col]) if t and t in w.index else np.nan)

    # Normalize: 1-9 → [-1, +1]
    for src_pref, dst_pref in [("l", "l"), ("o", "o"), ("x", "x")]:
        for d_code in ["v", "a", "d"]:
            src = f"{src_pref}{d_code}_raw"
            dst = f"{dst_pref}{d_code}"
            df[dst] = (df[src] - 5.0) / 4.0

    return df

# ── Bootstrap ────────────────────────────────────────────────────────────
def boot_ci(x, y, n_iter, rng):
    n = len(x); dist = np.empty(n_iter)
    for i in range(n_iter):
        idx = rng.choice(n, size=n, replace=True)
        dist[i], _ = stats.pearsonr(x[idx], y[idx])
    return np.quantile(dist, [0.025, 0.5, 0.975])

# ── Analysis ─────────────────────────────────────────────────────────────
def run_comparison(df, x_pfx, y_pfx, label):
    dim_codes = ["v", "a", "d"]
    dim_names = ["valence", "arousal", "dominance"]
    x_cols = [f"{x_pfx}{d}" for d in dim_codes]
    y_cols = [f"{y_pfx}{d}" for d in dim_codes]
    sub = df.dropna(subset=x_cols + y_cols)
    res = {"label": label, "n": len(sub)}
    for d_code, dim_name in zip(dim_codes, dim_names):
        xc, yc = f"{x_pfx}{d_code}", f"{y_pfx}{d_code}"
        v = sub[[xc, yc]].dropna()
        n = len(v)
        if n < 3:
            res[dim_name] = {"n": n, "error": "too few points"}; continue
        r, p = stats.pearsonr(v[xc], v[yc])
        rho, p2 = stats.spearmanr(v[xc], v[yc])
        s, i = np.polyfit(v[xc], v[yc], 1)
        ci = boot_ci(v[xc].values, v[yc].values, N_BOOT, rng)
        res[dim_name] = {
            "n": n, "pearson_r": round(float(r),4), "pearson_p": round(float(p),4),
            "spearman_rho": round(float(rho),4), "spearman_p": round(float(p2),4),
            "slope": round(float(s),4), "intercept": round(float(i),4),
            "ci_lo": round(float(ci[0]),4), "ci_mid": round(float(ci[1]),4),
            "ci_hi": round(float(ci[2]),4),
        }
    return res

# ── Figures ───────────────────────────────────────────────────────────────
def make_summary_grid(df, analyses):
    """3-row × 3-col: each row = one comparison, each col = one dimension."""
    comps = [
        ("x","o","① Lexical → Stimulus (n=17)"),
        ("o","l","② Stimulus → Experience (n=40)"),
        ("x","l","③ Lexical → Experience (n=17)"),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(15, 12.5), facecolor="white")

    for ri, (xp, yp, title) in enumerate(comps):
        for ci, dc in enumerate(["v","a","d"]):
            ax = axes[ri, ci]
            xc, yc = f"{xp}{dc}", f"{yp}{dc}"
            v = df[[xc, yc]].dropna()
            if len(v) < 3: continue
            xv, yv = v[xc].values, v[yc].values

            ax.scatter(xv, yv, c=DIM_COLORS[dc], s=55, alpha=0.75,
                       edgecolors="white", linewidth=0.6, zorder=3)
            s, inter = np.polyfit(xv, yv, 1)
            xl = np.linspace(xv.min()-0.3, xv.max()+0.3, 50)
            ax.plot(xl, s*xl+inter, color="#333", lw=1.3, ls="--", alpha=0.6)
            lo, hi = min(xv.min(),yv.min())-0.25, max(xv.max(),yv.max())+0.25
            ax.plot([lo,hi],[lo,hi], color="#D0D5D9", lw=0.6, ls=":", zorder=1)

            ck = f"{xp}_vs_{yp}"; dim_name = DIM_MAP[dc]
            r = analyses.get(ck, {}).get(dim_name, {})
            txt = (f"r={r.get('pearson_r',0):+.3f}  n={r.get('n',0)}\n"
                   f"CI [{r.get('ci_lo',0):+.2f}, {r.get('ci_hi',0):+.2f}]")
            fw = "bold" if abs(r.get("pearson_r",0)) > 0.3 else "normal"
            ax.text(0.03, 0.95, txt, transform=ax.transAxes, fontsize=8,
                    color="#3D4349", va="top", family="monospace", fontweight=fw)

            if ci == 0: ax.set_ylabel({"x":"Warriner","o":"Online","l":"Lab"}[yp], fontsize=10, color="#3D4349")
            if ri == 2: ax.set_xlabel({"x":"Warriner","o":"Online","l":"Lab"}[xp], fontsize=10, color="#3D4349")
            if ri == 0: ax.set_title(DIM_SHORT[dc], fontsize=12, fontweight="bold", color="#20272B")
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            ax.grid(True, alpha=0.15, color="#BAC1C7")

        axes[ri,0].text(-0.38, 0.5, title, transform=axes[ri,0].transAxes,
                        fontsize=10, fontweight="bold", color="#20272B", va="center",
                        ha="right", rotation=90)

    fig.suptitle("DEAP Three-Way VAD Decomposition", fontsize=15, fontweight="bold",
                 color="#20272B", y=1.01)
    fig.tight_layout()
    for ext in ["png","svg"]:
        fig.savefig(RESULTS / f"summary_grid.{ext}", dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)

def make_breakdown_bar(analyses):
    """Bar chart showing r for each comparison × dimension."""
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor="white")
    dims_p = ["valence","arousal","dominance"]
    comps_p = [("x_vs_o","Lexical→Stimulus","#2E7D6F"),
               ("o_vs_l","Stimulus→Experience","#D6862D"),
               ("x_vs_l","Lexical→Experience","#5E6670")]
    xp = np.arange(len(dims_p)); w = 0.22
    for j, (ck, cl, cc) in enumerate(comps_p):
        vals, los, his = [], [], []
        for d in dims_p:
            r = analyses.get(ck, {}).get(d, {})
            vals.append(r.get("pearson_r", 0))
            los.append(r.get("ci_lo", 0)); his.append(r.get("ci_hi", 0))
        err = [[max(0, v-l) for v,l in zip(vals,los)],
               [max(0, h-v) for v,h in zip(vals,his)]]
        off = (j-1)*w
        ax.bar(xp+off, vals, w, color=cc, label=cl, zorder=3, edgecolor="white", lw=0.5)
        ax.errorbar(xp+off, vals, yerr=err, fmt="none", ecolor="#333", capsize=4, lw=0.8)
    ax.axhline(y=0, color="#D0D5D9", lw=0.7, zorder=1)
    ax.set_xticks(xp); ax.set_xticklabels(["Valence","Arousal","Dominance"], fontsize=12)
    ax.set_ylabel("Pearson r", fontsize=11, color="#3D4349")
    ax.legend(frameon=False, fontsize=9, ncol=3, loc="upper right")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.grid(True, alpha=0.15, color="#BAC1C7", axis="y")
    ax.set_ylim(-0.6, 1.0)
    fig.suptitle("DEAP: Where Does Alignment Break?", fontsize=12, fontweight="bold",
                 color="#20272B", y=1.02)
    fig.tight_layout()
    for ext in ["png","svg"]:
        fig.savefig(RESULTS / f"breakdown.{ext}", dpi=200, facecolor="white", bbox_inches="tight")
    plt.close(fig)

def make_detail_figures(df, analyses):
    """Three separate detailed scatter figures, one per comparison."""
    configs = [
        ("x","o","① Lexical → Stimulus","Warriner","Online VAD","x_vs_o"),
        ("o","l","② Stimulus → Experience","Online VAD","Lab VAD","o_vs_l"),
        ("x","l","③ Lexical → Experience","Warriner","Lab VAD","x_vs_l"),
    ]
    for xp, yp, title, xlbl, ylbl, ck in configs:
        fig, axes = plt.subplots(1, 3, figsize=(16, 5), facecolor="white")
        for ci, dc in enumerate(["v","a","d"]):
            ax = axes[ci]; xc, yc = f"{xp}{dc}", f"{yp}{dc}"
            v = df[[xc, yc]].dropna()
            if len(v) < 3: continue
            xv, yv = v[xc].values, v[yc].values
            ax.scatter(xv, yv, c=DIM_COLORS[dc], s=65, alpha=0.78,
                       edgecolors="white", lw=0.6, zorder=3)
            s, inter = np.polyfit(xv, yv, 1)
            xl2 = np.linspace(xv.min()-0.25, xv.max()+0.25, 50)
            ax.plot(xl2, s*xl2+inter, color="#333", lw=1.3, ls="--", alpha=0.6)
            lo, hi = min(xv.min(),yv.min())-0.2, max(xv.max(),yv.max())+0.2
            ax.plot([lo,hi],[lo,hi], color="#D0D5D9", lw=0.7, ls=":", zorder=1)

            dim_name = DIM_MAP[dc]; r = analyses.get(ck, {}).get(dim_name, {})
            txt = (f"r = {r.get('pearson_r',0):+.3f} (p={r.get('pearson_p',0):.3f})\n"
                   f"ρ = {r.get('spearman_rho',0):+.3f}\nn = {r.get('n',0)}\n"
                   f"slope = {r.get('slope',0):.3f}")
            ax.text(0.03, 0.95, txt, transform=ax.transAxes, fontsize=8.2,
                    color="#3D4349", va="top", family="monospace")
            ax.set_xlabel(xlbl, fontsize=10, color="#3D4349")
            ax.set_ylabel(ylbl, fontsize=10, color="#3D4349")
            ax.set_title(DIM_FULL[dc], fontsize=12, fontweight="bold", color="#20272B")
            ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
            ax.grid(True, alpha=0.15, color="#BAC1C7")
        fig.suptitle(title, fontsize=13, fontweight="bold", color="#20272B", y=1.02)
        fig.tight_layout()
        for ext in ["png","svg"]:
            fig.savefig(RESULTS / f"{ck}.{ext}", dpi=200, facecolor="white", bbox_inches="tight")
        plt.close(fig)

# ── Main ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("DEAP Three-Way VAD Decomposition")
    print("=" * 60)

    df = load_all()
    n_tagged = int((df["tag"].str.len() > 0).sum())
    print(f"Data: {len(df)} videos, {n_tagged} with Warriner tags, 40 with Online + Lab VAD")

    a1 = run_comparison(df, "x", "o", "Lexical→Stimulus")
    a2 = run_comparison(df, "o", "l", "Stimulus→Experience")
    a3 = run_comparison(df, "x", "l", "Lexical→Experience")
    analyses = {"x_vs_o": a1, "o_vs_l": a2, "x_vs_l": a3}

    for key, a in analyses.items():
        print(f"\n{'─'*50}")
        print(f"  {a['label']} (n={a['n']})")
        print(f"  {'Dimension':<12} {'n':>3} {'r':>8} {'p':>8} {'ρ':>8} {'slope':>8} {'CI(95%)':>28}")
        for d in ["valence", "arousal", "dominance"]:
            r = a.get(d, {})
            if r.get("n", 0) > 0:
                print(f"  {d:<12} {r['n']:>3} {r['pearson_r']:>+8.3f} {r['pearson_p']:>8.4f} "
                      f"{r['spearman_rho']:>+8.3f} {r['slope']:>+8.3f} "
                      f"[{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]")

    # DREAMER baseline
    print(f"\n  {'─'*50}")
    print(f"  DREAMER baseline (NRC-VAD → Elicited, n=9)")
    for d, r_val, p_val in [("valence",0.875,".018"),("arousal",0.832,".034"),("dominance",-0.121,".792")]:
        print(f"  {d:<12}    r={r_val:+.3f}  Holm p={p_val}")

    # Variance diagnostic
    print(f"\n  {'─'*50}")
    print(f"  Variance (σ):")
    for lbl, pf in [("Lexical (tagged, n=17)","x"),("Online (all, n=40)","o"),("Lab (all, n=40)","l")]:
        s = [float(df[f"{pf}{d}"].std()) for d in ["v","a","d"]]
        print(f"    {lbl:<28}: ({s[0]:.3f}, {s[1]:.3f}, {s[2]:.3f})")

    # Figures
    print(f"\nGenerating figures...")
    make_summary_grid(df, analyses)
    make_breakdown_bar(analyses)
    make_detail_figures(df, analyses)

    # Save CSVs
    rows = []
    for ck, a in analyses.items():
        for d in ["valence", "arousal", "dominance"]:
            entry = dict(a.get(d, {}))
            entry["comparison"] = ck; entry["dimension"] = d; rows.append(entry)
    pd.DataFrame(rows).to_csv(RESULTS / "three_way_results.csv", index=False, float_format="%.4f")
    df.to_csv(RESULTS / "merged_vad_data.csv", index=False, float_format="%.4f")

    json.dump({
        "analysis": "DEAP three-way VAD decomposition",
        "participants": 32, "videos": 40, "videos_with_lexical_tags": n_tagged,
        "bootstrap_iterations": N_BOOT, "random_seed": SEED,
        "scale": "All sources: (X-5)/4, 1-9 → [-1,+1]",
        "comparisons": {
            "1": f"Lexical→Stimulus (n={a1['n']})",
            "2": f"Stimulus→Experience (n={a2['n']})",
            "3": f"Lexical→Experience (n={a3['n']})",
        }
    }, open(RESULTS / "run_manifest.json", "w"), indent=2, ensure_ascii=False)

    print(f"\nAll outputs → {RESULTS}\nDone.")

if __name__ == "__main__":
    main()
