"""
NRC 偏差 vs. Savaliya 人类共识率 — 2D + 3D 对比分析
=====================================================
同时用 V+A (2D) 和 V+A+D (3D) 分析 NRC 坐标偏差与
人类共识率的关系，测试 Dominance 维度是否提供额外解释力。
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

# (consensus_rate, is_exact_from_thesis)
CONSENSUS = {
    "Excited":      (84.0, True),
    "Depressed":    (78.0, True),
    "Nervous":      (57.0, True),
    "Amazed":       (78.0, False),
    "Horrified":    (77.0, False),
    "Grossed out":  (75.0, False),
    "Impartial":    (73.0, False),
    "Hostile":      (68.0, False),
    "Detached":     (67.0, False),
    "Disappointed": (63.0, False),
    "Sarcastic":    (60.0, False),
    "Anxious":      (55.0, False),
    "Astound":      (50.0, False),
    "Fed up":       (45.0, False),
}

BASE_EMOTIONS = ["Happy", "Sad", "Disgusted", "Fear", "Angry", "Surprised", "Neutral"]
LABEL_TO_NRC = {
    "Happy": "happy", "Sad": "sad", "Angry": "angry", "Fear": "fear",
    "Disgusted": "disgust", "Surprised": "surprise", "Neutral": "neutral",
}

OUTPUT_GRID = {
    "Happy": {
        "Happy": "joyful", "Sad": "nostalgic", "Disgusted": "amused",
        "Fear": "nervous", "Angry": "excited", "Surprised": "calm", "Neutral": "content",
    },
    "Sad": {
        "Happy": "bittersweet", "Sad": "depressed", "Disgusted": "disillusioned",
        "Fear": "dreadful", "Angry": "grieved", "Surprised": "sorrowful", "Neutral": "disappointed",
    },
    "Disgusted": {
        "Happy": "smug", "Sad": "despondent", "Disgusted": "nauseated",
        "Fear": "appalled", "Angry": "fed up", "Surprised": "grossed out", "Neutral": "unimpressed",
    },
    "Fear": {
        "Happy": "anxious", "Sad": "hopeless", "Disgusted": "horrified",
        "Fear": "petrified", "Angry": "terrified", "Surprised": "stunned", "Neutral": "cautious",
    },
    "Angry": {
        "Happy": "sarcastic", "Sad": "frustration", "Disgusted": "repulsed",
        "Fear": "hostile", "Angry": "furious", "Surprised": "shocked", "Neutral": "unaffected",
    },
    "Surprised": {
        "Happy": "amazed", "Sad": "disturbed", "Disgusted": "grossed out",
        "Fear": "alarmed", "Angry": "startled", "Surprised": "astound", "Neutral": "unfazed",
    },
    "Neutral": {
        "Happy": "neutral", "Sad": "indifferent", "Disgusted": "detached",
        "Fear": "cautious", "Angry": "unbothered", "Surprised": "unsurprised", "Neutral": "impartial",
    },
}

ALIASES = {
    "disillusioned": "disillusionment", "repulsed": "repulsion",
    "grossed out": "gross", "nauseated": "nausea",
}


# ============================================================
# NRC loading (supports V, A, D)
# ============================================================

def load_nrc_full(path: str) -> dict[str, tuple[float, float, float]]:
    """Load NRC VAD as {term: (V, A, D)}."""
    lex = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        # header: term, valence, arousal, dominance
        for raw in f:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            term = parts[0].lower().strip()
            if term in lex:
                continue
            lex[term] = (float(parts[1]), float(parts[2]), float(parts[3]))
    return lex


def get_nrc_va(term: str, full_lex: dict, ndim: int = 3) -> np.ndarray | None:
    """Resolve NRC coordinates for a term. Returns (V,A) or (V,A,D)."""
    t = term.lower().strip()
    if t in full_lex:
        return np.array(full_lex[t][:ndim], dtype=float)
    if t in ALIASES and ALIASES[t] in full_lex:
        return np.array(full_lex[ALIASES[t]][:ndim], dtype=float)
    # Multi-word decomposition
    if " " in t:
        parts = [p for p in t.split(" ") if p]
        part_vas = []
        for p in parts:
            if p in full_lex:
                part_vas.append(full_lex[p][:ndim])
            elif p in ALIASES and ALIASES[p] in full_lex:
                part_vas.append(full_lex[ALIASES[p]][:ndim])
        if part_vas:
            arr = np.array(part_vas, dtype=float)
            return np.mean(arr, axis=0)
    return None


# ============================================================
# Core computation (works for any dimension)
# ============================================================

def compute_metrics_nd(rows_out: list, ndim: int, dim_labels: list[str]):
    """Fill rows with NRC deviation metrics in N-dim space."""
    nrc_path = "data/NRC-VAD-Lexicon-v2.1.txt"
    full_lex = load_nrc_full(nrc_path)
    print(f"\n--- {ndim}D Analysis ({', '.join(dim_labels)}) ---")

    for r in rows_out:
        face_va = get_nrc_va(LABEL_TO_NRC[r["face"]], full_lex, ndim)
        voice_va = get_nrc_va(LABEL_TO_NRC[r["voice"]], full_lex, ndim)
        output_va = get_nrc_va(r["output_label"], full_lex, ndim)

        if any(x is None for x in [face_va, voice_va, output_va]):
            continue

        d = voice_va - face_va
        denom = np.dot(d, d)
        if denom > 1e-12:
            t_raw = float(np.dot(output_va - face_va, d) / denom)
            t_clipped = float(np.clip(t_raw, 0.0, 1.0))
            closest = face_va + t_clipped * d
        else:
            t_raw, t_clipped = 0.5, 0.5
            closest = face_va

        segment_dist = float(np.sqrt(np.sum((output_va - closest) ** 2)))
        midpoint = (face_va + voice_va) / 2.0
        midpoint_dist = float(np.sqrt(np.sum((output_va - midpoint) ** 2)))
        fv_dist = float(np.sqrt(denom))
        mid_dev_norm = midpoint_dist / (fv_dist + 1e-12)

        # Store in row with dimension prefix
        r[f"segdist_{ndim}d"] = segment_dist
        r[f"middist_{ndim}d"] = midpoint_dist
        r[f"middev_{ndim}d"] = mid_dev_norm
        r[f"fvdist_{ndim}d"] = fv_dist
        r[f"traw_{ndim}d"] = t_raw
        r[f"outside_{ndim}d"] = bool(t_raw < 0 or t_raw > 1)
        r[f"midpoint_vec_{ndim}d"] = tuple(float(x) for x in midpoint)

    valid = [r for r in rows_out if f"segdist_{ndim}d" in r]
    print(f"  Valid entries: {len(valid)}/{len(rows_out)}")
    return valid


# ============================================================
# Main analysis
# ============================================================

def main():
    out_dir = "report_assets/nrc_vs_consensus"
    os.makedirs(out_dir, exist_ok=True)

    # Build rows for 14 validated emotions
    rows_14 = []
    for face, voice, output_label in TABLE14:
        cons_info = CONSENSUS.get(output_label)
        if cons_info is None:
            continue
        rows_14.append({
            "face": face, "voice": voice, "output_label": output_label,
            "consensus_rate": cons_info[0], "consensus_exact": cons_info[1],
        })

    # Compute 2D and 3D metrics
    compute_metrics_nd(rows_14, 2, ["Valence", "Arousal"])
    compute_metrics_nd(rows_14, 3, ["Valence", "Arousal", "Dominance"])

    # ============================================================
    # Correlation analysis: 2D vs 3D
    # ============================================================
    from scipy.stats import pearsonr, spearmanr

    print(f"\n{'='*70}")
    print(f"CORRELATION: NRC DEVIATION vs HUMAN CONSENSUS (n={len(rows_14)})")
    print(f"{'='*70}")

    consensus = np.array([r["consensus_rate"] for r in rows_14])
    is_exact = np.array([r["consensus_exact"] for r in rows_14])

    for ndim, label in [(2, "2D (V+A)"), (3, "3D (V+A+D)")]:
        seg = np.array([r[f"segdist_{ndim}d"] for r in rows_14])
        mid = np.array([r[f"middist_{ndim}d"] for r in rows_14])
        dev = np.array([r[f"middev_{ndim}d"] for r in rows_14])

        print(f"\n{label}:")
        for name, vals in [("segment_dist", seg), ("midpoint_dist", mid), ("mid_dev_norm", dev)]:
            rp, pp = pearsonr(vals, consensus)
            rs, ps = spearmanr(vals, consensus)
            print(f"  {name:18s}: Pearson r={rp:+.3f} (p={pp:.3f})  Spearman rho={rs:+.3f} (p={ps:.3f})")

        # Exact-only
        if is_exact.sum() >= 3:
            rp_ex, pp_ex = pearsonr(mid[is_exact], consensus[is_exact])
            print(f"  {'exact-only midpoint':18s}: Pearson r={rp_ex:+.3f} (p={pp_ex:.3f}, n={is_exact.sum()})")

    # ============================================================
    # Detailed per-emotion table (2D vs 3D comparison)
    # ============================================================
    print(f"\n{'='*70}")
    print(f"PER-EMOTION COMPARISON (sorted by consensus)")
    print(f"{'='*70}")
    rows_sorted = sorted(rows_14, key=lambda r: -r["consensus_rate"])
    header = (f"{'Emotion':<14} {'Cons':>5} {'Exact':>5} | "
              f"{'2D_mid':>7} {'2D_seg':>7} {'2D_t':>7} | "
              f"{'3D_mid':>7} {'3D_seg':>7} {'3D_t':>7} | "
              f"{'Delta_mid':>9}")
    print(header)
    print("-" * len(header))
    for r in rows_sorted:
        d2_mid = r["middist_2d"]
        d3_mid = r["middist_3d"]
        delta = d3_mid - d2_mid
        print(f"{r['output_label']:<14} {r['consensus_rate']:>5.0f}% {str(r['consensus_exact']):>5} | "
              f"{d2_mid:>7.3f} {r['segdist_2d']:>7.3f} {r['traw_2d']:>+7.3f} | "
              f"{d3_mid:>7.3f} {r['segdist_3d']:>7.3f} {r['traw_3d']:>+7.3f} | "
              f"{delta:>+9.4f}")

    # Delta stats
    deltas = [r["middist_3d"] - r["middist_2d"] for r in rows_14]
    print(f"\n  Delta (3D_mid - 2D_mid): mean={mean(deltas):+.4f}, range=[{min(deltas):+.4f}, {max(deltas):+.4f}]")
    print(f"  Adding D {'INCREASES' if mean(deltas) > 0 else 'DECREASES'} midpoint distance on average")

    # Which emotions change most with D?
    print(f"\n  Emotions where D most changes the picture:")
    abs_deltas = sorted(zip([r["output_label"] for r in rows_14], deltas), key=lambda x: -abs(x[1]))
    for label, d in abs_deltas[:5]:
        direction = "farther from midpoint" if d > 0 else "closer to midpoint"
        print(f"    {label:<14}: {d:+.4f} ({direction})")

    # ============================================================
    # Which dimensions matter most?
    # ============================================================
    print(f"\n{'='*70}")
    print(f"DIMENSION CONTRIBUTIONS (per-coordinate deviation from midpoint)")
    print(f"{'='*70}")
    nrc_path = "data/NRC-VAD-Lexicon-v2.1.txt"
    full_lex = load_nrc_full(nrc_path)

    v_devs, a_devs, d_devs = [], [], []
    for r in rows_14:
        face_va = get_nrc_va(LABEL_TO_NRC[r["face"]], full_lex, 3)
        voice_va = get_nrc_va(LABEL_TO_NRC[r["voice"]], full_lex, 3)
        output_va = get_nrc_va(r["output_label"], full_lex, 3)
        midpoint = (face_va + voice_va) / 2.0
        dev = output_va - midpoint
        v_devs.append(abs(dev[0]))
        a_devs.append(abs(dev[1]))
        d_devs.append(abs(dev[2]))

    print(f"  Mean |V deviation| from midpoint: {mean(v_devs):.3f}")
    print(f"  Mean |A deviation| from midpoint: {mean(a_devs):.3f}")
    print(f"  Mean |D deviation| from midpoint: {mean(d_devs):.3f}")
    print(f"  V contributes {mean(v_devs)/(mean(v_devs)+mean(a_devs)+mean(d_devs))*100:.0f}% of total deviation")
    print(f"  A contributes {mean(a_devs)/(mean(v_devs)+mean(a_devs)+mean(d_devs))*100:.0f}% of total deviation")
    print(f"  D contributes {mean(d_devs)/(mean(v_devs)+mean(a_devs)+mean(d_devs))*100:.0f}% of total deviation")

    # ============================================================
    # Extend to full 49 cells in 3D
    # ============================================================
    print(f"\n{'='*70}")
    print(f"FULL 49 PREDICTED CONSENSUS (3D)")
    print(f"{'='*70}")

    all_rows = []
    for face in BASE_EMOTIONS:
        for voice in BASE_EMOTIONS:
            output_label = OUTPUT_GRID[face][voice]
            face_va = get_nrc_va(LABEL_TO_NRC[face], full_lex, 3)
            voice_va = get_nrc_va(LABEL_TO_NRC[voice], full_lex, 3)
            output_va = get_nrc_va(output_label, full_lex, 3)

            if any(x is None for x in [face_va, voice_va, output_va]):
                continue

            d = voice_va - face_va
            denom = np.dot(d, d)
            midpoint = (face_va + voice_va) / 2.0
            midpoint_dist = float(np.sqrt(np.sum((output_va - midpoint) ** 2)))
            fv_dist = float(np.sqrt(denom))

            # Deviation per dimension
            dev = output_va - midpoint
            v_dev = float(abs(dev[0]))
            a_dev = float(abs(dev[1]))
            d_dev = float(abs(dev[2]))

            is_validated = any(r["face"] == face and r["voice"] == voice for r in rows_14)

            all_rows.append({
                "face": face, "voice": voice, "output_label": output_label,
                "middist_3d": midpoint_dist, "fvdist_3d": fv_dist,
                "v_dev": v_dev, "a_dev": a_dev, "d_dev": d_dev,
                "is_validated": is_validated,
            })

    # Fit linear model and predict
    known_mid = np.array([r["middist_3d"] for r in rows_14])
    known_cons = np.array([r["consensus_rate"] for r in rows_14])
    slope, intercept = np.polyfit(known_mid, known_cons, 1)

    for r in all_rows:
        r["predicted_consensus_3d"] = max(0, min(100, slope * r["middist_3d"] + intercept))

    all_sorted = sorted(all_rows, key=lambda r: r["predicted_consensus_3d"])

    print(f"\n3D Linear model: consensus = {slope:.2f} * midpoint_dist + {intercept:.2f}")
    print(f"\nTop 10 LOWEST predicted consensus:")
    for r in all_sorted[:10]:
        v = "YES" if r["is_validated"] else "no"
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"mid={r['middist_3d']:.3f} pred={r['predicted_consensus_3d']:.0f}% [{v}]")

    print(f"\nTop 10 HIGHEST predicted consensus:")
    for r in all_sorted[-10:][::-1]:
        v = "YES" if r["is_validated"] else "no"
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"mid={r['middist_3d']:.3f} pred={r['predicted_consensus_3d']:.0f}% [{v}]")

    # Heatmap
    print(f"\n3D PREDICTED CONSENSUS HEATMAP:")
    print(f"{'':>10}", end="")
    for v in BASE_EMOTIONS:
        print(f"{v:>10}", end="")
    print()
    for face in BASE_EMOTIONS:
        print(f"{face:>10}", end="")
        for voice in BASE_EMOTIONS:
            matched = [r for r in all_rows if r["face"] == face and r["voice"] == voice]
            if matched:
                pc = matched[0]["predicted_consensus_3d"]
                print(f"{pc:>10.0f}", end="")
            else:
                print(f"{'N/A':>10}", end="")
        print()

    # Dimension deviation heatmap
    print(f"\nDOMINANCE DEVIATION HEATMAP (|D_output - D_midpoint|):")
    print(f"{'':>10}", end="")
    for v in BASE_EMOTIONS:
        print(f"{v:>10}", end="")
    print()
    for face in BASE_EMOTIONS:
        print(f"{face:>10}", end="")
        for voice in BASE_EMOTIONS:
            matched = [r for r in all_rows if r["face"] == face and r["voice"] == voice]
            if matched:
                print(f"{matched[0]['d_dev']:>10.3f}", end="")
            else:
                print(f"{'N/A':>10}", end="")
        print()

    # Save
    # Clean rows for CSV (remove tuple fields)
    clean_14 = []
    for r in rows_14:
        cr = {k: v for k, v in r.items() if not isinstance(v, tuple)}
        clean_14.append(cr)
    fieldnames_14 = sorted({k for cr in clean_14 for k in cr.keys()})
    with open(os.path.join(out_dir, "nrc_deviation_vs_consensus_2d3d.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_14)
        writer.writeheader()
        writer.writerows(clean_14)

    fieldnames_49 = sorted({k for r in all_rows for k in r.keys()})
    with open(os.path.join(out_dir, "full49_predicted_consensus_3d.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_49)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nDone. Output: {out_dir}")


if __name__ == "__main__":
    main()
