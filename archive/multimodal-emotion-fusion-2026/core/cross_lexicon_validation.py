"""
NRC VAD vs ANEW 跨词典交叉验证
===============================
用两本独立词典的 VAD 坐标，对 Savaliya 14 个复杂情绪
计算 F-V 中点偏差，与人类共识率做相关分析。
"""
import csv
import math
import os
from statistics import mean, stdev

import numpy as np

# ============================================================
# Data
# ============================================================

TABLE14 = [
    ("Happy", "Fear", "Nervous"),
    ("Happy", "Angry", "Excited"),
    ("Sad", "Sad", "Depressed"),
    ("Sad", "Neutral", "Disappointed"),
    ("Disgusted", "Angry", "Fed up"),
    ("Disgusted", "Surprised", "Grossed out"),
    ("Fear", "Happy", "Anxious"),
    ("Fear", "Disgusted", "Horrified"),
    ("Angry", "Happy", "Sarcastic"),
    ("Angry", "Fear", "Hostile"),
    ("Surprised", "Happy", "Amazed"),
    ("Surprised", "Angry", "Astound"),
    ("Neutral", "Disgusted", "Detached"),
    ("Neutral", "Neutral", "Impartial"),
]

CONSENSUS = {
    "Excited": 84.0, "Depressed": 78.0, "Nervous": 57.0,
    "Amazed": 78.0, "Horrified": 77.0, "Grossed out": 75.0,
    "Impartial": 73.0, "Hostile": 68.0, "Detached": 67.0,
    "Disappointed": 63.0, "Sarcastic": 60.0, "Anxious": 55.0,
    "Astound": 50.0, "Fed up": 45.0,
}

BASE_EMOTIONS = ["Happy", "Sad", "Disgusted", "Fear", "Angry", "Surprised", "Neutral"]
LABEL_TO_NRC = {
    "Happy": "happy", "Sad": "sad", "Angry": "angry", "Fear": "fear",
    "Disgusted": "disgust", "Surprised": "surprise", "Neutral": "neutral",
}

# The output term might differ from NRC term for some lexicon lookups
OUTPUT_TERMS = {
    "Nervous": "nervous", "Excited": "excited", "Depressed": "depressed",
    "Disappointed": "disappointed", "Fed up": "fed up", "Grossed out": "grossed out",
    "Anxious": "anxious", "Horrified": "horrified", "Sarcastic": "sarcastic",
    "Hostile": "hostile", "Amazed": "amazed", "Astound": "astound",
    "Detached": "detached", "Impartial": "impartial",
}

ALIASES_NRC = {
    "disillusioned": "disillusionment", "repulsed": "repulsion",
    "grossed out": "gross", "nauseated": "nausea",
}

ALIASES_ANEW = {
    "grossed out": "gross",
    "fed up": "fedup",  # ANEW might have "fed up" as one word
}


def load_nrc(path: str) -> dict[str, np.ndarray]:
    lex = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.readline()
        for raw in f:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            term = parts[0].lower().strip()
            if term not in lex:
                lex[term] = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
    return lex


def load_anew(path: str) -> dict[str, np.ndarray]:
    """Load ANEW from BRM-emot-submit.csv. Uses V.Mean.Sum, A.Mean.Sum, D.Mean.Sum."""
    lex = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        cols = header.strip().split(",")
        # Find column indices
        word_idx = cols.index("Word")
        v_idx = cols.index("V.Mean.Sum")
        a_idx = cols.index("A.Mean.Sum")
        d_idx = cols.index("D.Mean.Sum")

        for raw in f:
            parts = raw.strip().split(",")
            if len(parts) < max(v_idx, a_idx, d_idx) + 1:
                continue
            term = parts[word_idx].lower().strip()
            if term in lex:
                continue
            try:
                v = float(parts[v_idx])
                a = float(parts[a_idx])
                d = float(parts[d_idx])
                lex[term] = np.array([v, a, d])
            except (ValueError, IndexError):
                continue
    return lex


def resolve_term(term_raw: str, lex: dict, aliases: dict) -> np.ndarray | None:
    """Resolve a term in a lexicon, trying exact match then aliases."""
    t = term_raw.lower().strip()
    if t in lex:
        return lex[t]
    if t in aliases and aliases[t] in lex:
        return lex[aliases[t]]
    # Multi-word fallback: average individual words
    if " " in t:
        parts = [p for p in t.split(" ") if p]
        arrs = []
        for p in parts:
            if p in lex:
                arrs.append(lex[p])
        if arrs:
            return np.mean(np.array(arrs), axis=0)
    return None


def compute_coverage_and_deviation(lex: dict, aliases: dict, lex_name: str):
    """Compute coverage and midpoint deviation for all 14 emotions."""
    results = []
    missing_base = set()
    missing_output = set()

    for face, voice, output_label in TABLE14:
        f_va = resolve_term(LABEL_TO_NRC[face], lex, aliases)
        v_va = resolve_term(LABEL_TO_NRC[voice], lex, aliases)
        o_va = resolve_term(output_label, lex, aliases)

        if f_va is None:
            missing_base.add(LABEL_TO_NRC[face])
        if v_va is None:
            missing_base.add(LABEL_TO_NRC[voice])
        if o_va is None:
            missing_output.add(output_label)

        if any(x is None for x in [f_va, v_va, o_va]):
            continue

        midpoint = (f_va + v_va) / 2.0
        dev = float(np.sqrt(np.sum((o_va - midpoint) ** 2)))
        consensus = CONSENSUS.get(output_label, 50.0)

        results.append({
            "face": face, "voice": voice, "output_label": output_label,
            "consensus": consensus,
            "dev_3d": dev,
            "o_v": float(o_va[0]), "o_a": float(o_va[1]), "o_d": float(o_va[2]),
            "mid_v": float(midpoint[0]), "mid_a": float(midpoint[1]),
            "mid_d": float(midpoint[2]),
            "f_v": float(f_va[0]), "f_a": float(f_va[1]), "f_d": float(f_va[2]),
            "v_v": float(v_va[0]), "v_a": float(v_va[1]), "v_d": float(v_va[2]),
        })

    n_base_total = 7
    n_output_total = 14
    base_cov = n_base_total - len(missing_base)
    output_cov = n_output_total - len(missing_output)

    print(f"\n{lex_name} coverage:")
    print(f"  Base emotions: {base_cov}/{n_base_total} ({100*base_cov/n_base_total:.0f}%)")
    if missing_base:
        print(f"    Missing: {sorted(missing_base)}")
    print(f"  Output labels: {output_cov}/{n_output_total} ({100*output_cov/n_output_total:.0f}%)")
    print(f"    Missing: {sorted(missing_output)}" if missing_output else "    All present")
    print(f"  Valid pairs: {len(results)}/14")

    return results, missing_base, missing_output


def main():
    nrc_path = "data/NRC-VAD-Lexicon-v2.1.txt"
    anew_path = "data/ANEW/BRM-emot-submit.csv"
    out_dir = "report_assets/cross_lexicon"
    os.makedirs(out_dir, exist_ok=True)

    # Load both lexicons
    lex_nrc = load_nrc(nrc_path)
    lex_anew = load_anew(anew_path)
    print(f"NRC VAD: {len(lex_nrc)} terms")
    print(f"ANEW:    {len(lex_anew)} terms")

    # Compute coverage and deviations for both
    nrc_results, nrc_mb, nrc_mo = compute_coverage_and_deviation(
        lex_nrc, ALIASES_NRC, "NRC VAD")
    anew_results, anew_mb, anew_mo = compute_coverage_and_deviation(
        lex_anew, ALIASES_ANEW, "ANEW (Warriner 2013)")

    # ============================================================
    # Correlation analysis: NRC vs ANEW
    # ============================================================
    from scipy.stats import pearsonr, spearmanr

    print(f"\n{'='*70}")
    print(f"CROSS-LEXICON CORRELATION WITH HUMAN CONSENSUS")
    print(f"{'='*70}")

    for name, results in [("NRC VAD", nrc_results), ("ANEW", anew_results)]:
        if len(results) < 5:
            print(f"\n{name}: insufficient data ({len(results)} pairs)")
            continue

        devs = np.array([r["dev_3d"] for r in results])
        conss = np.array([r["consensus"] for r in results])
        rp, pp = pearsonr(devs, conss)
        rs, ps = spearmanr(devs, conss)
        print(f"\n{name} (n={len(results)}):")
        print(f"  Pearson r = {rp:+.3f} (p={pp:.4f})")
        print(f"  Spearman rho = {rs:+.3f} (p={ps:.4f})")
        print(f"  Mean deviation = {mean(devs):.3f}")

    # ============================================================
    # Overlap analysis: compare NRC and ANEW on shared terms
    # ============================================================
    print(f"\n{'='*70}")
    print(f"NRC vs ANEW DIRECT COMPARISON (shared pairs only)")
    print(f"{'='*70}")

    # Find pairs present in both lexicons
    nrc_by_label = {r["output_label"]: r for r in nrc_results}
    anew_by_label = {r["output_label"]: r for r in anew_results}
    shared_labels = set(nrc_by_label.keys()) & set(anew_by_label.keys())
    print(f"Shared validated pairs: {len(shared_labels)}/14")

    if len(shared_labels) >= 5:
        # Compare deviations
        print(f"\n{'Emotion':<14} {'Cons':>5} {'NRC dev':>8} {'ANEW dev':>8} {'Delta':>8} {'Agree?':>7}")
        print("-" * 55)
        for label in sorted(shared_labels, key=lambda l: -CONSENSUS.get(l, 0)):
            d_nrc = nrc_by_label[label]["dev_3d"]
            d_anew = anew_by_label[label]["dev_3d"]
            delta = d_anew - d_nrc
            agree = "YES" if (d_nrc > 0.5) == (d_anew > 0.5) else "DIFFER"
            print(f"{label:<14} {CONSENSUS.get(label,0):>5.0f}% {d_nrc:>8.3f} {d_anew:>8.3f} "
                  f"{delta:>+8.3f} {agree:>7}")

        # Correlation between NRC and ANEW deviations
        nrc_devs = [nrc_by_label[l]["dev_3d"] for l in shared_labels]
        anew_devs = [anew_by_label[l]["dev_3d"] for l in shared_labels]
        r_na, p_na = pearsonr(nrc_devs, anew_devs)
        print(f"\nNRC vs ANEW deviation correlation: r={r_na:+.3f} (p={p_na:.4f})")
        print(f"  -> The two lexicons {'AGREE' if r_na > 0.5 else 'PARTIALLY AGREE' if r_na > 0.2 else 'DISAGREE'} on which emotions deviate most")

        # Which lexicon has larger deviations?
        nrc_mean = mean(nrc_devs)
        anew_mean = mean(anew_devs)
        print(f"  Mean deviation: NRC={nrc_mean:.3f}, ANEW={anew_mean:.3f}")
        print(f"  -> ANEW has {'LARGER' if anew_mean > nrc_mean else 'SMALLER'} deviations on average")

    # ============================================================
    # Coordinate-level comparison
    # ============================================================
    print(f"\n{'='*70}")
    print(f"COORDINATE-LEVEL NRC vs ANEW COMPARISON")
    print(f"{'='*70}")

    # For the 7 base emotions, compare NRC and ANEW coordinates directly
    print(f"\nBase emotion coordinates (NRC vs ANEW):")
    print(f"{'Emotion':<12} {'NRC V':>7} {'NRC A':>7} {'NRC D':>7} | {'ANEW V':>7} {'ANEW A':>7} {'ANEW D':>7} | {'dist':>7}")
    print("-" * 75)
    for face in BASE_EMOTIONS:
        term = LABEL_TO_NRC[face]
        nrc_va = resolve_term(term, lex_nrc, {})
        anew_va = resolve_term(term, lex_anew, {})
        if nrc_va is not None and anew_va is not None:
            dist = float(np.sqrt(np.sum((nrc_va - anew_va) ** 2)))
            print(f"{face:<12} {nrc_va[0]:>+7.3f} {nrc_va[1]:>+7.3f} {nrc_va[2]:>+7.3f} | "
                  f"{anew_va[0]:>+7.3f} {anew_va[1]:>+7.3f} {anew_va[2]:>+7.3f} | {dist:>7.3f}")
        elif nrc_va is not None:
            print(f"{face:<12} {nrc_va[0]:>+7.3f} {nrc_va[1]:>+7.3f} {nrc_va[2]:>+7.3f} | {'MISSING':>21} |")
        else:
            print(f"{face:<12} {'MISSING in NRC':>21} | {anew_va[0]:>+7.3f} {anew_va[1]:>+7.3f} {anew_va[2]:>+7.3f} |")

    # Save
    all_nrc = [{**r, "lexicon": "NRC"} for r in nrc_results]
    all_anew = [{**r, "lexicon": "ANEW"} for r in anew_results]
    all_rows = all_nrc + all_anew

    fieldnames = sorted({k for r in all_rows for k in r.keys()})
    with open(os.path.join(out_dir, "cross_lexicon_results.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nDone. Output: {out_dir}")


if __name__ == "__main__":
    main()
