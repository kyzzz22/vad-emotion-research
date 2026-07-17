"""
NRC 覆盖率审计 + 精确匹配 vs 降级查询性能差异 + Permutation test + 质化分析
构建方向 C 核心叙事所需的全部数据
"""
import csv
import math
import os
import sys
from collections import defaultdict
from statistics import mean, stdev

import numpy as np

import train_dual_channel_extended as base_model


# ============================================================
# Part 1: NRC 覆盖率审计 — 每个输出词的匹配质量
# ============================================================

OUTPUT_TERM_GRID = {
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

BASE_EMOTIONS = ["Happy", "Sad", "Disgusted", "Fear", "Angry", "Surprised", "Neutral"]
BASE_TO_NRC_TERM = {
    "Happy": "happy", "Sad": "sad", "Angry": "angry", "Fear": "fear",
    "Disgusted": "disgust", "Surprised": "surprise", "Neutral": "neutral",
}

ALIASES = {
    "disillusioned": "disillusionment",
    "repulsed": "repulsion",
    "grossed out": "gross",
    "nauseated": "nausea",
}


def load_full_nrc(path: str) -> dict[str, tuple[float, float]]:
    """Load ALL terms from NRC VAD (not just a filtered subset)."""
    lex = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        for raw in f:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            term = parts[0].lower().strip()
            if term in lex:
                continue
            lex[term] = (float(parts[1]), float(parts[2]))
    return lex


def normalize_term(t: str) -> str:
    return " ".join(t.strip().lower().split())


def classify_term(term_raw: str, full_lex: dict) -> dict:
    """Determine HOW a term gets its NRC VA coordinate."""
    t = normalize_term(term_raw)

    # Case 1: Exact match
    if t in full_lex:
        return {
            "term": term_raw,
            "normalized": t,
            "match_type": "exact",
            "va": full_lex[t],
            "via": t,
        }

    # Case 2: Alias match
    if t in ALIASES and ALIASES[t] in full_lex:
        return {
            "term": term_raw,
            "normalized": t,
            "match_type": "alias",
            "va": full_lex[ALIASES[t]],
            "via": f"{t} -> {ALIASES[t]}",
        }

    # Case 3: Multi-word decomposition
    if " " in t:
        parts = [p for p in t.split(" ") if p]
        part_vas = []
        part_details = []
        for p in parts:
            if p in full_lex:
                part_vas.append(full_lex[p])
                part_details.append(f"{p}(exact)")
            elif p in ALIASES and ALIASES[p] in full_lex:
                part_vas.append(full_lex[ALIASES[p]])
                part_details.append(f"{p}->{ALIASES[p]}")
            else:
                part_details.append(f"{p}(MISSING)")
        if part_vas:
            v = float(np.mean([x[0] for x in part_vas]))
            a = float(np.mean([x[1] for x in part_vas]))
            return {
                "term": term_raw,
                "normalized": t,
                "match_type": "multi_word",
                "va": (v, a),
                "via": " + ".join(part_details),
                "parts_missing": len(parts) - len(part_vas),
            }

    # Case 4: Missing entirely
    return {
        "term": term_raw,
        "normalized": t,
        "match_type": "MISSING",
        "va": None,
        "via": "NOT FOUND",
    }


def audit_all_terms(nrc_path: str):
    """Audit all 49 output terms + 7 base terms."""
    full_lex = load_full_nrc(nrc_path)
    print(f"NRC VAD total terms loaded: {len(full_lex)}")

    rows = []
    all_output_terms = set()
    for f in BASE_EMOTIONS:
        for v in BASE_EMOTIONS:
            all_output_terms.add(OUTPUT_TERM_GRID[f][v])
    for t in BASE_TO_NRC_TERM.values():
        all_output_terms.add(t)

    for term_raw in sorted(all_output_terms):
        info = classify_term(term_raw, full_lex)
        rows.append(info)

    # Summary statistics
    exact_count = sum(1 for r in rows if r["match_type"] == "exact")
    alias_count = sum(1 for r in rows if r["match_type"] == "alias")
    mw_count = sum(1 for r in rows if r["match_type"] == "multi_word")
    missing_count = sum(1 for r in rows if r["match_type"] == "MISSING")

    print(f"\n=== NRC Coverage Summary (all {len(rows)} unique terms) ===")
    print(f"  Exact match:    {exact_count}/{len(rows)} ({100*exact_count/len(rows):.0f}%)")
    print(f"  Alias:          {alias_count}/{len(rows)} ({100*alias_count/len(rows):.0f}%)")
    print(f"  Multi-word avg: {mw_count}/{len(rows)} ({100*mw_count/len(rows):.0f}%)")
    print(f"  MISSING:        {missing_count}/{len(rows)} ({100*missing_count/len(rows):.0f}%)")

    # Now report per-cell match quality
    print(f"\n=== 7x7 Grid -- per-cell match quality ===")
    print(f"{'Face':>10} x {'Voice':<10} | {'Output Term':<16} | {'Match Type':<12} | {'V':>16} | {'A':>16} | Via")
    print("-" * 130)

    cell_rows = []
    for f in BASE_EMOTIONS:
        for v in BASE_EMOTIONS:
            term_raw = OUTPUT_TERM_GRID[f][v]
            info = classify_term(term_raw, full_lex)
            cell_rows.append({
                "face": f, "voice": v, **info,
            })
            va_v = f"{info['va'][0]:+.4f}" if info['va'] else "None"
            va_a = f"{info['va'][1]:+.4f}" if info['va'] else "None"
            print(f"{f:>10} x {v:<10} | {term_raw:<16} | {info['match_type']:<12} | V={va_v:>8} A={va_a:>8} | {info['via']}")

    # Diagonal override check
    print(f"\n=== Diagonal Override Check ===")
    for l in BASE_EMOTIONS:
        label_term = BASE_TO_NRC_TERM[l]
        output_term = OUTPUT_TERM_GRID[l][l]
        label_info = classify_term(label_term, full_lex)
        output_info = classify_term(output_term, full_lex)
        if label_info["va"] and output_info["va"]:
            dist = math.sqrt((label_info["va"][0] - output_info["va"][0])**2 +
                           (label_info["va"][1] - output_info["va"][1])**2)
            print(f"  {l}x{l}: label='{label_term}' {label_info['va']}  "
                  f"output='{output_term}' {output_info['va']}  "
                  f"dist={dist:.4f}  {'!! OVERRIDDEN' if dist < 1e-9 else 'ok different'}")

    return rows, cell_rows, full_lex


# ============================================================
# Part 2: Exact-match vs Approximated subset analysis
# ============================================================

def run_subset_analysis(nrc_path: str, cell_rows: list, out_dir: str):
    """Run Table14->Holdout35 separately on exact-match vs approximated cells."""
    labels, table_full = base_model.full49_table_nrc_direct(nrc_path)

    # Classify each of the 49 cells
    exact_pairs = set()
    approx_pairs = set()
    for cr in cell_rows:
        pair = f"{cr['face']}|{cr['voice']}"
        if cr["match_type"] == "exact":
            exact_pairs.add(pair)
        else:
            approx_pairs.add(pair)

    print(f"\n=== Subset Analysis ===")
    print(f"Exact-match cells: {len(exact_pairs)}/49")
    print(f"Approximated cells: {len(approx_pairs)}/49")

    base_coords = {k: np.array(table_full[k][k], dtype=float) for k in labels}
    X_list, y_list, pairs_list = [], [], []
    for f in labels:
        for v in labels:
            F = base_coords[f]
            V = base_coords[v]
            E = np.array(table_full[f][v], dtype=float)
            X_list.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
            y_list.append([float(E[0]), float(E[1])])
            pairs_list.append(f"{f}|{v}")
    X_full = np.array(X_list, dtype=float)
    y_full = np.array(y_list, dtype=float)
    pairs_full = pairs_list

    # For each subset: we still train on Table14 (which spans both subsets),
    # but evaluate Holdout separately for exact vs. approx
    X_train, y_train, _, train_pairs = base_model.build_dataset_table14_from_table(labels, table_full)

    # Find holdout indices for exact and approx subsets
    train_set = set(train_pairs)
    holdout_exact_idx = [i for i, p in enumerate(pairs_full) if p not in train_set and p in exact_pairs]
    holdout_approx_idx = [i for i, p in enumerate(pairs_full) if p not in train_set and p in approx_pairs]

    print(f"Holdout exact-match: {len(holdout_exact_idx)} cells")
    print(f"Holdout approximated: {len(holdout_approx_idx)} cells")

    # Train best linear model on Table14
    CASES4 = base_model.CASES4 if hasattr(base_model, 'CASES4') else [
        ("ap_bp", "B", "pos"), ("ap_bn", "B", "neg"),
        ("an_bp", "C", "pos"), ("an_bn", "C", "neg"),
    ]
    seeds = list(range(12))

    best_model = None
    best_loss = float("inf")
    for form in ["linear", "abs"]:
        for case in CASES4:
            case_name, constraint, b_sign = case
            trials = [
                base_model.train_adam(
                    X_train, y_train, seed=seed, steps=4000, lr=0.05,
                    form=form, constraint=constraint, b_sign=b_sign, l2=0.0,
                )
                for seed in seeds
            ]
            trials.sort(key=lambda d: d["loss"])
            if trials[0]["loss"] < best_loss:
                best_loss = trials[0]["loss"]
                best_model = {
                    "method": form, "case": case_name,
                    "params": np.array(trials[0]["params"], dtype=float),
                }

    def predict(model_info, X):
        pred, _, _ = base_model.forward(model_info["params"], X, form=model_info["method"])
        return pred

    # Evaluate on each subset
    results = {}
    for name, idx in [("exact", holdout_exact_idx), ("approx", holdout_approx_idx), ("all_holdout", holdout_exact_idx + holdout_approx_idx)]:
        if not idx:
            results[name] = {"mse": None, "r2_v": None, "r2_a": None, "n": 0}
            continue
        X_sub = X_full[idx]
        y_sub = y_full[idx]
        pred_sub = predict(best_model, X_sub)
        results[name] = {
            "mse": float(base_model.mse(y_sub, pred_sub)),
            "r2_v": float(base_model.r2_score(y_sub[:, 0], pred_sub[:, 0])),
            "r2_a": float(base_model.r2_score(y_sub[:, 1], pred_sub[:, 1])),
            "n": len(idx),
        }

    for name, r in results.items():
        print(f"  {name} (n={r['n']}): MSE={r['mse']:.4f}, R2_V={r['r2_v']:.4f}, R2_A={r['r2_a']:.4f}")

    return results


# ============================================================
# Part 3: Permutation Test
# ============================================================

def run_permutation_test(nrc_path: str, n_permutations: int = 200, out_dir: str = "report_assets/permutation_test"):
    """Randomly shuffle output labels and measure how often we get MSE as good as real.

    Uses ridge regression (closed-form, fast) instead of Adam for the permutation test
    since we just need a consistent model, not the best possible model.
    """
    os.makedirs(out_dir, exist_ok=True)

    labels, table_real = base_model.full49_table_nrc_direct(nrc_path)
    base_coords = {k: np.array(table_real[k][k], dtype=float) for k in labels}
    X_list, y_list, pairs_list = [], [], []
    for f in labels:
        for v in labels:
            F = base_coords[f]
            V = base_coords[v]
            E = np.array(table_real[f][v], dtype=float)
            X_list.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
            y_list.append([float(E[0]), float(E[1])])
            pairs_list.append(f"{f}|{v}")
    X_full = np.array(X_list, dtype=float)
    y_full = np.array(y_list, dtype=float)
    pairs_full = pairs_list
    X_train, y_train, _, train_pairs = base_model.build_dataset_table14_from_table(labels, table_real)

    # Real performance using best linear model (consistent with previous experiments)
    seeds = list(range(8))
    real_results = []
    for form in ["linear"]:
        for case_name in ["ap_bp", "ap_bn", "an_bp", "an_bn"]:
            constraint = "B" if case_name.startswith("ap") else "C"
            b_sign = "pos" if case_name.endswith("bp") else "neg"
            trials = [
                base_model.train_adam(
                    X_train, y_train, seed=seed, steps=3000, lr=0.05,
                    form=form, constraint=constraint, b_sign=b_sign, l2=0.0,
                )
                for seed in seeds
            ]
            trials.sort(key=lambda d: d["loss"])
            params = np.array(trials[0]["params"], dtype=float)
            pred_full, _, _ = base_model.forward(params, X_full, form=form)

            train_idx = [i for i, p in enumerate(pairs_full) if p in train_pairs]
            holdout_idx = [i for i, p in enumerate(pairs_full) if p not in train_pairs]

            real_results.append({
                "form": form, "case": case_name,
                "train_mse": float(base_model.mse(y_full[train_idx], pred_full[train_idx])),
                "holdout_mse": float(base_model.mse(y_full[holdout_idx], pred_full[holdout_idx])),
            })

    real_best = min(real_results, key=lambda r: r["holdout_mse"])
    real_holdout_mse = real_best["holdout_mse"]
    print(f"\n=== Permutation Test ===")
    print(f"Real best holdout MSE: {real_holdout_mse:.4f} ({real_best['form']}_{real_best['case']})")
    print(f"Running {n_permutations} permutations (using closed-form ridge regression for speed)...")

    # Collect all output coordinates
    all_output_coords = []
    for f in labels:
        for v in labels:
            all_output_coords.append(tuple(table_real[f][v]))

    train_idx = [i for i, p in enumerate(pairs_full) if p in train_pairs]
    holdout_idx = [i for i, p in enumerate(pairs_full) if p not in train_pairs]

    def ridge_fit_predict(X_tr, y_tr, X_te, alpha=0.1):
        """Closed-form ridge regression: predict VA from [F_v, F_a, V_v, V_a]."""
        X_aug = np.column_stack([np.ones((len(X_tr), 1)), X_tr])
        reg = np.eye(X_aug.shape[1]) * alpha
        reg[0, 0] = 0  # Don't penalize intercept
        W = np.linalg.solve(X_aug.T @ X_aug + reg, X_aug.T @ y_tr)
        X_te_aug = np.column_stack([np.ones((len(X_te), 1)), X_te])
        return X_te_aug @ W

    permuted_mses = []
    for perm_i in range(n_permutations):
        # Shuffle output coordinates
        shuffled = list(all_output_coords)
        np.random.shuffle(shuffled)
        y_perm = np.array(shuffled, dtype=float).reshape(49, 2)

        yt_perm = y_perm[train_idx]
        pred = ridge_fit_predict(X_full[train_idx], yt_perm, X_full)
        mse_perm = float(base_model.mse(y_perm[holdout_idx], pred[holdout_idx]))
        permuted_mses.append(mse_perm)

        if (perm_i + 1) % 50 == 0:
            p_val_est = sum(1 for m in permuted_mses if m <= real_holdout_mse) / len(permuted_mses)
            print(f"  {perm_i+1}/{n_permutations} done, p~{p_val_est:.4f}")

    permuted_mses = np.array(permuted_mses)
    n_better_or_equal = int(np.sum(permuted_mses <= real_holdout_mse))
    p_value = n_better_or_equal / n_permutations

    print(f"\n=== Permutation Test Results ===")
    print(f"Real holdout MSE: {real_holdout_mse:.4f}")
    print(f"Permuted MSE mean: {permuted_mses.mean():.4f}")
    print(f"Permuted MSE std:  {permuted_mses.std():.4f}")
    print(f"Permuted MSE min:  {permuted_mses.min():.4f}")
    print(f"Permuted MSE max:  {permuted_mses.max():.4f}")
    print(f"Times permuted <= real: {n_better_or_equal}/{n_permutations}")
    print(f"p-value (one-sided): {p_value:.4f}")

    # Effect size
    cohens_d = (real_holdout_mse - permuted_mses.mean()) / permuted_mses.std() if permuted_mses.std() > 0 else 0
    print(f"Cohen's d: {cohens_d:.4f}")

    # Save
    np.save(os.path.join(out_dir, "permuted_mses.npy"), permuted_mses)
    with open(os.path.join(out_dir, "permutation_results.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value"])
        writer.writerow(["real_holdout_mse", real_holdout_mse])
        writer.writerow(["permuted_mean", float(permuted_mses.mean())])
        writer.writerow(["permuted_std", float(permuted_mses.std())])
        writer.writerow(["permuted_min", float(permuted_mses.min())])
        writer.writerow(["permuted_max", float(permuted_mses.max())])
        writer.writerow(["n_better_or_equal", n_better_or_equal])
        writer.writerow(["n_permutations", n_permutations])
        writer.writerow(["p_value", p_value])
        writer.writerow(["cohens_d", cohens_d])

    return {
        "real_mse": real_holdout_mse,
        "permuted_mean": float(permuted_mses.mean()),
        "permuted_std": float(permuted_mses.std()),
        "p_value": p_value,
        "cohens_d": cohens_d,
        "n_permutations": n_permutations,
    }


# ============================================================
# Part 4: Qualitative analysis of deviant cells
# ============================================================

def analyze_deviant_cells(nrc_path: str, cell_rows: list, full_lex: dict, out_dir: str):
    """Deep-dive on the cells with largest segment distance."""
    os.makedirs(out_dir, exist_ok=True)

    labels, table = base_model.full49_table_nrc_direct(nrc_path)
    base_coords = {k: np.array(table[k][k], dtype=float) for k in labels}
    X_list, y_list, pairs_list = [], [], []
    for f in labels:
        for v in labels:
            F = base_coords[f]
            V = base_coords[v]
            E = np.array(table[f][v], dtype=float)
            X_list.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
            y_list.append([float(E[0]), float(E[1])])
            pairs_list.append(f"{f}|{v}")
    X_full = np.array(X_list, dtype=float)
    y_full = np.array(y_list, dtype=float)
    pairs_full = pairs_list

    # Compute segment distances
    F = X_full[:, 0:2]
    V = X_full[:, 2:4]
    d = V - F
    denom = np.sum(d * d, axis=1)
    raw_t = np.zeros(len(X_full))
    valid = denom > 1e-12
    raw_t[valid] = np.sum((y_full[valid] - F[valid]) * d[valid], axis=1) / denom[valid]
    t = np.clip(raw_t, 0.0, 1.0)
    closest = F + t[:, None] * d
    dist = np.sqrt(np.sum((y_full - closest) ** 2, axis=1))
    outside = (raw_t < 0.0) | (raw_t > 1.0)

    # For each cell, find nearest NRC words
    def find_nearby_words(target_va: tuple, lex: dict, top_k: int = 15, min_dist: float = 0.0):
        results = []
        for term, va in lex.items():
            d = math.sqrt((target_va[0] - va[0])**2 + (target_va[1] - va[1])**2)
            if d >= min_dist:
                results.append((term, va, d))
        results.sort(key=lambda x: x[2])
        return results[:top_k]

    # Build analysis rows
    analysis_rows = []
    for i, pair in enumerate(pairs_full):
        f_label, v_label = pair.split("|")
        output_term = OUTPUT_TERM_GRID[f_label][v_label]
        match_info = classify_term(output_term, full_lex)

        row = {
            "pair": pair,
            "face": f_label,
            "voice": v_label,
            "output_term": output_term,
            "match_type": match_info["match_type"],
            "segment_dist": float(dist[i]),
            "raw_t": float(raw_t[i]),
            "outside_segment": bool(outside[i]),
            "face_v": float(F[i, 0]), "face_a": float(F[i, 1]),
            "voice_v": float(V[i, 0]), "voice_a": float(V[i, 1]),
            "target_v": float(y_full[i, 0]), "target_a": float(y_full[i, 1]),
            "closest_on_segment_v": float(closest[i, 0]),
            "closest_on_segment_a": float(closest[i, 1]),
        }

        # NRC nearest neighbors
        target_va = (float(y_full[i, 0]), float(y_full[i, 1]))
        nearby = find_nearby_words(target_va, full_lex, top_k=10)
        row["nrc_nn_1"] = f"{nearby[0][0]} (d={nearby[0][2]:.4f})" if nearby else ""
        row["nrc_nn_2"] = f"{nearby[1][0]} (d={nearby[1][2]:.4f})" if len(nearby) > 1 else ""
        row["nrc_nn_3"] = f"{nearby[2][0]} (d={nearby[2][2]:.4f})" if len(nearby) > 2 else ""

        # Midpoint and simple average location
        mid_v = (float(F[i, 0]) + float(V[i, 0])) / 2
        mid_a = (float(F[i, 1]) + float(V[i, 1])) / 2
        row["midpoint_v"] = mid_v
        row["midpoint_a"] = mid_a
        row["midpoint_dist"] = math.sqrt((float(y_full[i, 0]) - mid_v)**2 + (float(y_full[i, 1]) - mid_a)**2)

        analysis_rows.append(row)

    # Sort by segment distance
    analysis_rows.sort(key=lambda r: r["segment_dist"], reverse=True)

    # Print top 15
    print(f"\n=== Top 15 Deviant Cells (largest F-V segment distance) ===")
    print(f"{'Rank':<5} {'Pair':<25} {'Term':<16} {'Match':<12} {'SegDist':>8} {'Out?':<6} {'MidDist':>8} {'NRC NN1'}")
    print("-" * 130)
    for rank, row in enumerate(analysis_rows[:15], 1):
        print(f"{rank:<5} {row['pair']:<25} {row['output_term']:<16} {row['match_type']:<12} "
              f"{row['segment_dist']:>8.4f} {'YES' if row['outside_segment'] else 'no':<6} "
              f"{row['midpoint_dist']:>8.4f} {row['nrc_nn_1']}")

    # Also list cells with largest NRC nearest-neighbor distance (dictionary sparsity)
    print(f"\n=== Top 15 Cells by NRC-NN Distance (dictionary sparsity) ===")
    analysis_rows_by_nn = sorted(analysis_rows, key=lambda r: float(r["nrc_nn_1"].split("d=")[1].rstrip(")")) if r["nrc_nn_1"] and "d=" in r["nrc_nn_1"] else 999)
    # Actually let's compute properly
    for row in analysis_rows:
        target_va = (row["target_v"], row["target_a"])
        nearby = find_nearby_words(target_va, full_lex, top_k=1)
        row["min_nrc_dist"] = nearby[0][2] if nearby else 999
    analysis_rows.sort(key=lambda r: r["min_nrc_dist"], reverse=True)
    for rank, row in enumerate(analysis_rows[:15], 1):
        print(f"{rank:<5} {row['pair']:<25} {row['output_term']:<16} {row['match_type']:<12} "
              f"min_nrc_dist={row['min_nrc_dist']:.4f}")

    # Restore segment-distance sort
    analysis_rows.sort(key=lambda r: r["segment_dist"], reverse=True)

    # Save
    fieldnames = sorted({k for row in analysis_rows for k in row.keys()})
    with open(os.path.join(out_dir, "deviant_cell_analysis.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_rows)

    return analysis_rows


# ============================================================
# Part 5: Procrustes-like analysis: decompose the difference
# ============================================================

def analyze_geometry_mismatch(nrc_path: str, out_dir: str):
    """Characterize HOW the native and nrc_direct geometries differ."""
    os.makedirs(out_dir, exist_ok=True)

    # Get both tables
    labels_native, table_native = base_model.full49_table_native()
    labels_direct, table_direct = base_model.full49_table_nrc_direct(nrc_path)

    def build_from_table(labels_t, table_t):
        base_t = {k: np.array(table_t[k][k], dtype=float) for k in labels_t}
        Xt, yt, pt = [], [], []
        for f in labels_t:
            for v in labels_t:
                F = base_t[f]
                V = base_t[v]
                E = np.array(table_t[f][v], dtype=float)
                Xt.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
                yt.append([float(E[0]), float(E[1])])
                pt.append(f"{f}|{v}")
        return np.array(Xt, dtype=float), np.array(yt, dtype=float), pt

    X_nat, y_nat, pairs = build_from_table(labels_native, table_native)
    X_dir, y_dir, _ = build_from_table(labels_direct, table_direct)

    # Compute per-cell vectors and compare
    rows = []
    for i, pair in enumerate(pairs):
        f_label, v_label = pair.split("|")
        # In native space
        f_nat = X_nat[i, 0:2]
        v_nat = X_nat[i, 2:4]
        out_nat = y_nat[i]
        d_nat = v_nat - f_nat

        # In NRC-direct space
        f_dir = X_dir[i, 0:2]
        v_dir = X_dir[i, 2:4]
        out_dir_coord = y_dir[i]
        d_dir = v_dir - f_dir

        # Where does the output lie relative to F-V line in each space?
        denom_nat = np.dot(d_nat, d_nat)
        denom_dir = np.dot(d_dir, d_dir)
        t_nat = np.dot(out_nat - f_nat, d_nat) / denom_nat if denom_nat > 1e-12 else 0.5
        t_dir = np.dot(out_dir_coord - f_dir, d_dir) / denom_dir if denom_dir > 1e-12 else 0.5

        # Distance of output from midpoint (normalized by F-V distance)
        mid_nat = (f_nat + v_nat) / 2
        mid_dir = (f_dir + v_dir) / 2
        fv_dist_nat = math.sqrt(denom_nat)
        fv_dist_dir = math.sqrt(denom_dir)
        mid_dev_nat = math.sqrt(np.sum((out_nat - mid_nat)**2)) / (fv_dist_nat + 1e-12)
        mid_dev_dir = math.sqrt(np.sum((out_dir_coord - mid_dir)**2)) / (fv_dist_dir + 1e-12)

        rows.append({
            "pair": pair,
            "face": f_label, "voice": v_label,
            "output_term": OUTPUT_TERM_GRID[f_label][v_label],
            "t_native": float(np.clip(t_nat, -2, 3)),
            "t_nrc_direct": float(np.clip(t_dir, -2, 3)),
            "t_shift": float(np.clip(t_dir, -2, 3)) - float(np.clip(t_nat, -2, 3)),
            "fv_dist_native": float(fv_dist_nat),
            "fv_dist_nrc_direct": float(fv_dist_dir),
            "mid_dev_native": float(mid_dev_nat),
            "mid_dev_nrc_direct": float(mid_dev_dir),
            "out_v_native": float(out_nat[0]), "out_a_native": float(out_nat[1]),
            "out_v_direct": float(out_dir_coord[0]), "out_a_direct": float(out_dir_coord[1]),
        })

    # Summary statistics
    t_shifts = [r["t_shift"] for r in rows]
    mid_dev_ratios = [r["mid_dev_nrc_direct"] / (r["mid_dev_native"] + 1e-12) for r in rows]

    print(f"\n=== Geometry Mismatch Characterization ===")
    print(f"t (position along F-V segment):")
    print(f"  native:     mean={mean([r['t_native'] for r in rows]):.3f}, std={stdev([r['t_native'] for r in rows]):.3f}")
    print(f"  nrc_direct: mean={mean([r['t_nrc_direct'] for r in rows]):.3f}, std={stdev([r['t_nrc_direct'] for r in rows]):.3f}")
    print(f"  t_shift:    mean={mean(t_shifts):.3f}, std={stdev(t_shifts):.3f}")
    print(f"  |t_shift| > 0.5: {sum(1 for s in t_shifts if abs(s) > 0.5)}/49 cells")
    print(f"  |t_shift| > 1.0: {sum(1 for s in t_shifts if abs(s) > 1.0)}/49 cells")
    print(f"Midpoint deviation ratio (direct/native): mean={mean(mid_dev_ratios):.2f}, median={sorted(mid_dev_ratios)[24]:.2f}")

    # Save
    out_path = os.path.join(str(out_dir), "geometry_mismatch.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for row in rows for k in row.keys()}))
        writer.writeheader()
        writer.writerows(rows)

    return rows


# ============================================================
# Main
# ============================================================

def main():
    nrc_path = "data/NRC-VAD-Lexicon-v2.1.txt"
    out_root = "report_assets/story_analysis"
    os.makedirs(out_root, exist_ok=True)

    print("=" * 70)
    print("PART 1: NRC Coverage Audit")
    print("=" * 70)
    term_rows, cell_rows, full_lex = audit_all_terms(nrc_path)

    print(f"\n{'=' * 70}")
    print("PART 2: Exact vs Approximated Subset Performance")
    print("=" * 70)
    subset_results = run_subset_analysis(nrc_path, cell_rows, out_root)

    print(f"\n{'=' * 70}")
    print("PART 3: Permutation Test")
    print("=" * 70)
    perm_results = run_permutation_test(nrc_path, n_permutations=500, out_dir=os.path.join(out_root, "permutation_test"))

    print(f"\n{'=' * 70}")
    print("PART 4: Deviant Cell Qualitative Analysis")
    print("=" * 70)
    deviant_rows = analyze_deviant_cells(nrc_path, cell_rows, full_lex, out_root)

    print(f"\n{'=' * 70}")
    print("PART 5: Geometry Mismatch Characterization")
    print("=" * 70)
    geom_rows = analyze_geometry_mismatch(nrc_path, out_root)

    # Final summary
    print(f"\n{'=' * 70}")
    print("STORY SYNTHESIS")
    print("=" * 70)

    exact_count = sum(1 for cr in cell_rows if cr["match_type"] == "exact")
    approx_count = sum(1 for cr in cell_rows if cr["match_type"] != "exact")

    print(f"""
KEY NUMBERS FOR THE STORY:

1. NRC Coverage: {exact_count}/49 output terms ({100*exact_count/49:.0f}%) have exact NRC matches.
   → {approx_count}/49 ({100*approx_count/49:.0f}%) require alias, multi-word decomposition, or are missing.

2. Permutation test: real holdout MSE = {perm_results['real_mse']:.4f}
   vs. permuted mean = {perm_results['permuted_mean']:.4f} ± {perm_results['permuted_std']:.4f}
   p = {perm_results['p_value']:.4f}, Cohen's d = {perm_results['cohens_d']:.4f}
   → {"Structure EXISTS beyond random labeling" if perm_results['p_value'] < 0.05 else "Structure NOT distinguishable from random"}

3. Geometry mismatch: the two spaces differ systematically.
   → See report_assets/story_analysis/ for detailed outputs.
""")

    print("Done. All outputs in:", out_root)


if __name__ == "__main__":
    main()
