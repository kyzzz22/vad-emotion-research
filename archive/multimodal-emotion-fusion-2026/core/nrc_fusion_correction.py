"""
NRC → Fusion 3D 校正模型
=========================
用 Savaliya 14 个人类验证点，训练从 NRC 词典坐标到
"多模态融合适用坐标"的校正函数。LOO 交叉验证 + 全 49 格预测。
"""
import csv
import math
import os
from statistics import mean, stdev

import numpy as np

# ============================================================
# Data (same as previous analyses)
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


def load_nrc_full(path: str) -> dict[str, tuple[float, float, float]]:
    lex = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.readline()
        for raw in f:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            term = parts[0].lower().strip()
            if term not in lex:
                lex[term] = (float(parts[1]), float(parts[2]), float(parts[3]))
    return lex


def get_nrc_3d(term: str, lex: dict) -> np.ndarray | None:
    t = term.lower().strip()
    if t in lex:
        return np.array(lex[t][:3], dtype=float)
    if t in ALIASES and ALIASES[t] in lex:
        return np.array(lex[ALIASES[t]][:3], dtype=float)
    if " " in t:
        parts = [p for p in t.split(" ") if p]
        arrs = []
        for p in parts:
            if p in lex:
                arrs.append(lex[p][:3])
            elif p in ALIASES and ALIASES[p] in lex:
                arrs.append(lex[ALIASES[p]][:3])
        if arrs:
            return np.mean(np.array(arrs, dtype=float), axis=0)
    return None


def load_training_data(nrc_path: str):
    """Extract 14 validated data points with NRC 3D coordinates."""
    lex = load_nrc_full(nrc_path)
    data = []
    for face, voice, output_label in TABLE14:
        f_va = get_nrc_3d(LABEL_TO_NRC[face], lex)
        v_va = get_nrc_3d(LABEL_TO_NRC[voice], lex)
        o_va = get_nrc_3d(output_label, lex)
        if any(x is None for x in [f_va, v_va, o_va]):
            continue
        midpoint = (f_va + v_va) / 2.0
        consensus = CONSENSUS.get(output_label, 50.0)
        data.append({
            "face": face, "voice": voice, "output_label": output_label,
            "F": f_va, "V": v_va, "O_nrc": o_va, "midpoint": midpoint,
            "consensus": consensus,
            "error_nrc": o_va - midpoint,  # current deviation
        })
    return data


# ============================================================
# Correction Models
# ============================================================

def fit_linear_correction(O_train: np.ndarray, midpoint_train: np.ndarray, alpha: float = 0.0):
    """
    Learn W (3x3) and b (3,) such that W @ O + b ≈ midpoint.
    Ridge regression: min ||O @ W^T + b - midpoint||^2 + alpha * ||W||^2
    """
    n = O_train.shape[0]
    # Augment with bias: [O | 1]
    X = np.column_stack([O_train, np.ones((n, 1), dtype=float)])
    # Solve for each output dimension independently
    reg = np.eye(4, dtype=float) * alpha
    reg[3, 3] = 0  # Don't penalize bias
    W_full = np.linalg.solve(X.T @ X + reg, X.T @ midpoint_train)
    W = W_full[:3, :].T  # 3x3
    b = W_full[3, :]     # (3,)
    return W, b


def apply_linear_correction(O: np.ndarray, W: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Apply correction: O_corrected = W @ O + b."""
    return (O @ W.T) + b


def fit_identity_plus_scale(O_train: np.ndarray, midpoint_train: np.ndarray):
    """
    Simpler model: O_corrected = O + diag(s) @ (midpoint - O)
    i.e. learn per-dimension scaling toward the midpoint.
    This is more interpretable: each dimension gets a shrinkage factor.
    """
    error = midpoint_train - O_train
    # For each dimension d, learn s_d: corrected[d] = O[d] + s_d * (midpoint[d] - O[d])
    # Equivalent to: corrected[d] = (1-s_d)*O[d] + s_d*midpoint[d]
    # Best s_d minimizes ||O[d] + s_d*(midpoint[d]-O[d]) - midpoint[d]||^2
    # = min ||(1-s_d)*(O[d] - midpoint[d])||^2 = 0 when s_d=1
    # That's just the midpoint. Let's try per-dimension ridge instead.
    s = np.zeros(3)
    for d in range(3):
        num = np.sum(error[:, d] * (midpoint_train[:, d] - O_train[:, d]))
        den = np.sum((midpoint_train[:, d] - O_train[:, d]) ** 2)
        s[d] = num / (den + 1e-12)
    # Clamp to reasonable range
    s = np.clip(s, -2.0, 2.0)
    return s


def apply_scale_correction(O: np.ndarray, s: np.ndarray, midpoint: np.ndarray) -> np.ndarray:
    """Apply scale correction: O_corrected = O + s * (midpoint - O)."""
    return O + s * (midpoint - O)


def fit_weighted_linear(O_train: np.ndarray, midpoint_train: np.ndarray,
                         consensus_train: np.ndarray, alpha: float = 0.0):
    """
    Weighted version: high-consensus emotions get more weight.
    """
    n = O_train.shape[0]
    weights = np.array(consensus_train, dtype=float) / 100.0
    X = np.column_stack([O_train, np.ones((n, 1), dtype=float)])
    W_weighted = X.T * weights
    reg = np.eye(4, dtype=float) * alpha
    reg[3, 3] = 0
    W_full = np.linalg.solve(W_weighted @ X + reg, W_weighted @ midpoint_train)
    W = W_full[:3, :].T
    b = W_full[3, :]
    return W, b


# ============================================================
# Leave-One-Out Cross-Validation
# ============================================================

def loo_evaluate(data: list, alpha: float = 0.0, use_weights: bool = False):
    """LOO CV for linear correction. Returns per-sample results."""
    results = []
    n = len(data)

    for i in range(n):
        # Training set: all except i
        train_idx = [j for j in range(n) if j != i]
        O_train = np.array([data[j]["O_nrc"] for j in train_idx])
        mid_train = np.array([data[j]["midpoint"] for j in train_idx])
        cons_train = np.array([data[j]["consensus"] for j in train_idx])

        # Test point
        O_test = np.array([data[i]["O_nrc"]])
        mid_test = np.array([data[i]["midpoint"]])
        F_test = np.array([data[i]["F"]])
        V_test = np.array([data[i]["V"]])

        # Fit
        if use_weights:
            W, b = fit_weighted_linear(O_train, mid_train, cons_train, alpha)
        else:
            W, b = fit_linear_correction(O_train, mid_train, alpha)

        # Predict
        O_corrected = apply_linear_correction(O_test, W, b)[0]

        # Also try scale model
        s = fit_identity_plus_scale(O_train, mid_train)
        O_scaled = apply_scale_correction(O_test, s, mid_test)[0]

        # Also compute simple average (no correction)
        O_avg = (F_test + V_test) / 2.0

        # Distances
        err_nrc = float(np.sqrt(np.sum((O_test[0] - mid_test[0]) ** 2)))
        err_corrected = float(np.sqrt(np.sum((O_corrected - mid_test[0]) ** 2)))
        err_scaled = float(np.sqrt(np.sum((O_scaled - mid_test[0]) ** 2)))
        err_avg = float(np.sqrt(np.sum((O_avg[0] - mid_test[0]) ** 2)))

        results.append({
            "face": data[i]["face"], "voice": data[i]["voice"],
            "output_label": data[i]["output_label"],
            "consensus": data[i]["consensus"],
            "err_nrc": err_nrc, "err_corrected": err_corrected,
            "err_scaled": err_scaled,
            "improvement": err_nrc - err_corrected,
            "improvement_pct": 100 * (err_nrc - err_corrected) / (err_nrc + 1e-12),
        })

    return results


# ============================================================
# Full prediction on 49 cells
# ============================================================

def predict_all_49(data_14: list, nrc_path: str, alpha: float = 0.0):
    """Train on all 14, predict correction for all 49 cells."""
    lex = load_nrc_full(nrc_path)

    # Train on all 14
    O_train = np.array([d["O_nrc"] for d in data_14])
    mid_train = np.array([d["midpoint"] for d in data_14])
    cons_train = np.array([d["consensus"] for d in data_14])

    W, b = fit_linear_correction(O_train, mid_train, alpha)

    # Apply to all 49
    all_rows = []
    for face in BASE_EMOTIONS:
        for voice in BASE_EMOTIONS:
            output_label = OUTPUT_GRID[face][voice]
            f_va = get_nrc_3d(LABEL_TO_NRC[face], lex)
            v_va = get_nrc_3d(LABEL_TO_NRC[voice], lex)
            o_va = get_nrc_3d(output_label, lex)

            if any(x is None for x in [f_va, v_va, o_va]):
                continue

            midpoint = (f_va + v_va) / 2.0
            O_corrected = apply_linear_correction(np.array([o_va]), W, b)[0]

            err_nrc = float(np.sqrt(np.sum((o_va - midpoint) ** 2)))
            err_corrected = float(np.sqrt(np.sum((O_corrected - midpoint) ** 2)))
            improvement = err_nrc - err_corrected

            # Is this one of the 14 validated?
            is_validated = any(d["face"] == face and d["voice"] == voice for d in data_14)

            all_rows.append({
                "face": face, "voice": voice, "output_label": output_label,
                "nrc_v": float(o_va[0]), "nrc_a": float(o_va[1]), "nrc_d": float(o_va[2]),
                "corrected_v": float(O_corrected[0]), "corrected_a": float(O_corrected[1]),
                "corrected_d": float(O_corrected[2]),
                "midpoint_v": float(midpoint[0]), "midpoint_a": float(midpoint[1]),
                "midpoint_d": float(midpoint[2]),
                "err_nrc": err_nrc, "err_corrected": err_corrected,
                "improvement": improvement,
                "is_validated": is_validated,
            })

    return all_rows, W, b


# ============================================================
# Main
# ============================================================

def main():
    nrc_path = "data/NRC-VAD-Lexicon-v2.1.txt"
    out_dir = "report_assets/nrc_fusion_correction"
    os.makedirs(out_dir, exist_ok=True)

    print("=" * 70)
    print("NRC -> FUSION 3D CORRECTION MODEL")
    print("=" * 70)

    data = load_training_data(nrc_path)
    print(f"Loaded {len(data)} validated emotions")

    # Baseline: NRC deviation stats
    errs_nrc = [float(np.sqrt(np.sum((d["O_nrc"] - d["midpoint"]) ** 2))) for d in data]
    print(f"\nBaseline NRC midpoint error: mean={mean(errs_nrc):.3f}, range=[{min(errs_nrc):.3f}, {max(errs_nrc):.3f}]")

    # LOO CV
    print(f"\n{'='*70}")
    print(f"LEAVE-ONE-OUT CROSS-VALIDATION")
    print(f"{'='*70}")

    results = loo_evaluate(data, alpha=0.01, use_weights=False)
    results_weighted = loo_evaluate(data, alpha=0.01, use_weights=True)

    print(f"\n{'Model':<25} {'Mean Err':>9} {'Std Err':>9} {'Mean Impr':>9} {'Impr %':>8}")
    print("-" * 65)
    for name, res in [("Linear (unweighted)", results), ("Linear (consensus-weighted)", results_weighted)]:
        errs = [r["err_corrected"] for r in res]
        imprs = [r["improvement"] for r in res]
        impr_pcts = [r["improvement_pct"] for r in res]
        print(f"{name:<25} {mean(errs):>9.4f} {stdev(errs):>9.4f} {mean(imprs):>9.4f} {mean(impr_pcts):>7.1f}%")

    # Per-emotion detail
    print(f"\n{'Emotion':<14} {'Cons':>5} {'Err NRC':>8} {'Err Corr':>8} {'Impr':>8} {'Scaled':>8}")
    print("-" * 60)
    for r in sorted(results, key=lambda r: r["improvement"]):
        print(f"{r['output_label']:<14} {r['consensus']:>5.0f}% {r['err_nrc']:>8.4f} "
              f"{r['err_corrected']:>8.4f} {r['improvement']:>+8.4f} {r['err_scaled']:>8.4f}")

    # Paired t-test
    from scipy.stats import ttest_rel
    t_stat, p_val = ttest_rel(
        [r["err_nrc"] for r in results],
        [r["err_corrected"] for r in results],
    )
    print(f"\nPaired t-test (NRC vs Corrected error): t={t_stat:.3f}, p={p_val:.4f}")
    if p_val < 0.05:
        print("  -> Correction SIGNIFICANTLY improves fit to midpoint")
    else:
        print("  -> Improvement NOT statistically significant (n=14 is too small)")

    # Check: does improvement correlate with consensus?
    from scipy.stats import pearsonr
    imprs = [r["improvement"] for r in results]
    conss = [r["consensus"] for r in results]
    r_ip, p_ip = pearsonr(imprs, conss)
    print(f"\nImprovement vs Consensus correlation: r={r_ip:.3f}, p={p_ip:.3f}")
    print(f"  -> {'More improvement for low-consensus emotions' if r_ip < 0 else 'Less improvement for low-consensus emotions'}")

    # ============================================================
    # Full 49 prediction
    # ============================================================
    print(f"\n{'='*70}")
    print(f"FULL 49 PREDICTION (trained on all 14)")
    print(f"{'='*70}")

    all_rows, W, b = predict_all_49(data, nrc_path, alpha=0.01)

    print(f"\nCorrection matrix W (3x3):")
    print(f"  [{W[0,0]:+.4f} {W[0,1]:+.4f} {W[0,2]:+.4f}]")
    print(f"  [{W[1,0]:+.4f} {W[1,1]:+.4f} {W[1,2]:+.4f}]")
    print(f"  [{W[2,0]:+.4f} {W[2,1]:+.4f} {W[2,2]:+.4f}]")
    print(f"Bias b: [{b[0]:+.4f}, {b[1]:+.4f}, {b[2]:+.4f}]")

    # Top improvements and deteriorations
    all_sorted = sorted(all_rows, key=lambda r: -r["improvement"])
    print(f"\nTop 10 MOST improved (NRC was far from midpoint, correction helps):")
    for r in all_sorted[:10]:
        v = " [VALIDATED]" if r["is_validated"] else ""
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"err: {r['err_nrc']:.3f} -> {r['err_corrected']:.3f} "
              f"(improvement: {r['improvement']:+.3f}){v}")

    print(f"\nTop 10 LEAST improved or DETERIORATED:")
    for r in all_sorted[-10:][::-1]:
        v = " [VALIDATED]" if r["is_validated"] else ""
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"err: {r['err_nrc']:.3f} -> {r['err_corrected']:.3f} "
              f"(improvement: {r['improvement']:+.3f}){v}")

    # ============================================================
    # Testable predictions for human experiment
    # ============================================================
    print(f"\n{'='*70}")
    print(f"TESTABLE PREDICTIONS (unvalidated cells only)")
    print(f"{'='*70}")

    unvalidated = [r for r in all_rows if not r["is_validated"]]

    # Sort by corrected error (largest = most likely to have low consensus)
    unvalidated_by_err = sorted(unvalidated, key=lambda r: -r["err_corrected"])

    print(f"\nPredicted LOWEST consensus (largest post-correction error):")
    print(f"  {'Face':>10} x {'Voice':<10} -> {'Label':<14} {'Pred Err':>8} {'NRC V':>7} {'NRC A':>7} {'NRC D':>7}")
    print(f"  {'':->60}")
    for r in unvalidated_by_err[:10]:
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"{r['err_corrected']:>8.3f} {r['nrc_v']:>+7.3f} {r['nrc_a']:>+7.3f} {r['nrc_d']:>+7.3f}")

    print(f"\nPredicted HIGHEST consensus (smallest post-correction error):")
    for r in unvalidated_by_err[-10:][::-1]:
        print(f"  {r['face']:>10} x {r['voice']:<10} -> {r['output_label']:<14} "
              f"{r['err_corrected']:>8.3f} {r['nrc_v']:>+7.3f} {r['nrc_a']:>+7.3f} {r['nrc_d']:>+7.3f}")

    # Save
    fieldnames_49 = sorted({k for r in all_rows for k in r.keys()})
    with open(os.path.join(out_dir, "full49_corrected.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_49)
        writer.writeheader()
        writer.writerows(all_rows)

    fieldnames_loo = sorted({k for r in results for k in r.keys()})
    with open(os.path.join(out_dir, "loo_cv_results.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_loo)
        writer.writeheader()
        writer.writerows(results)

    # Save correction matrix
    with open(os.path.join(out_dir, "correction_matrix.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["row", "col", "value"])
        for i in range(3):
            for j in range(3):
                writer.writerow([f"W_{i}{j}", j, W[i, j]])
        for i in range(3):
            writer.writerow([f"b_{i}", "", b[i]])

    print(f"\nDone. Outputs: {out_dir}")


if __name__ == "__main__":
    main()
