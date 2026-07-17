import argparse
import math
import random
import os

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def softplus(x: np.ndarray) -> np.ndarray:
    return np.log1p(np.exp(-np.abs(x))) + np.maximum(x, 0)


def transform_sign(x_raw: float, sign: str, eps: float = 0.0) -> tuple[float, float]:
    if sign == "free":
        return x_raw, 1.0
    if sign == "pos":
        x = float(softplus(np.array(x_raw))) + eps
        dx = float(sigmoid(np.array(x_raw)))
        return x, dx
    if sign == "neg":
        x = -(float(softplus(np.array(x_raw))) + eps)
        dx = -float(sigmoid(np.array(x_raw)))
        return x, dx
    raise ValueError("sign must be one of: free, pos, neg")


def base_emotion_coords() -> dict[str, np.ndarray]:
    labels = ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]
    table: dict[str, dict[str, tuple[float, float]]] = {
        "Happy": {
            "Happy": (0.8, 0.6),
            "Sad": (-0.27, -0.35),
            "Disgusted": (0.1, 0.6),
            "Fear": (0.0, 0.75),
            "Angry": (0.05, 0.7),
            "Surprised": (0.7, 0.8),
            "Neutral": (0.4, 0.3),
        },
        "Sad": {
            "Happy": (-0.14, 0.0),
            "Sad": (-0.7, -0.5),
            "Disgusted": (-0.6, 0.1),
            "Fear": (-0.75, 0.2),
            "Angry": (-0.6, 0.2),
            "Surprised": (-0.2, 0.2),
            "Neutral": (-0.35, -0.25),
        },
        "Angry": {
            "Happy": (0.2, 0.5),
            "Sad": (-0.5, 0.1),
            "Disgusted": (-0.7, 0.7),
            "Fear": (-0.75, 0.85),
            "Angry": (-0.7, 0.8),
            "Surprised": (-0.2, 0.9),
            "Neutral": (-0.44, 0.42),
        },
        "Fear": {
            "Happy": (0.0, 0.7),
            "Sad": (-0.7, 0.2),
            "Disgusted": (-0.7, 0.75),
            "Fear": (-0.8, 0.9),
            "Angry": (-0.8, 0.85),
            "Surprised": (-0.2, 0.9),
            "Neutral": (-0.2, 0.5),
        },
        "Disgusted": {
            "Happy": (0.1, 0.5),
            "Sad": (-0.6, 0.1),
            "Disgusted": (-0.6, 0.6),
            "Fear": (-0.7, 0.75),
            "Angry": (-0.7, 0.7),
            "Surprised": (-0.1, 0.8),
            "Neutral": (-0.3, 0.2),
        },
        "Surprised": {
            "Happy": (0.7, 0.8),
            "Sad": (-0.2, 0.2),
            "Disgusted": (-0.1, 0.8),
            "Fear": (-0.2, 0.9),
            "Angry": (-0.2, 0.9),
            "Surprised": (0.4, 0.9),
            "Neutral": (0.2, 0.4),
        },
        "Neutral": {
            "Happy": (0.4, 0.3),
            "Sad": (-0.35, -0.25),
            "Disgusted": (-0.3, 0.2),
            "Fear": (-0.2, 0.5),
            "Angry": (-0.4, 0.4),
            "Surprised": (0.2, 0.4),
            "Neutral": (0.0, 0.0),
        },
    }
    return {k: np.array(table[k][k], dtype=float) for k in labels}


def full49_table_native() -> tuple[list[str], dict[str, dict[str, tuple[float, float]]]]:
    labels = ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]
    table: dict[str, dict[str, tuple[float, float]]] = {
        "Happy": {
            "Happy": (0.8, 0.6),
            "Sad": (-0.27, -0.35),
            "Angry": (0.05, 0.7),
            "Fear": (0.0, 0.75),
            "Disgusted": (0.1, 0.6),
            "Surprised": (0.7, 0.8),
            "Neutral": (0.4, 0.3),
        },
        "Sad": {
            "Happy": (-0.14, 0.0),
            "Sad": (-0.7, -0.5),
            "Angry": (-0.6, 0.2),
            "Fear": (-0.75, 0.2),
            "Disgusted": (-0.6, 0.1),
            "Surprised": (-0.2, 0.2),
            "Neutral": (-0.35, -0.25),
        },
        "Angry": {
            "Happy": (0.2, 0.5),
            "Sad": (-0.5, 0.1),
            "Angry": (-0.7, 0.8),
            "Fear": (-0.75, 0.85),
            "Disgusted": (-0.7, 0.7),
            "Surprised": (-0.2, 0.9),
            "Neutral": (-0.44, 0.42),
        },
        "Fear": {
            "Happy": (0.0, 0.7),
            "Sad": (-0.7, 0.2),
            "Angry": (-0.8, 0.85),
            "Fear": (-0.8, 0.9),
            "Disgusted": (-0.7, 0.75),
            "Surprised": (-0.2, 0.9),
            "Neutral": (-0.2, 0.5),
        },
        "Disgusted": {
            "Happy": (0.1, 0.5),
            "Sad": (-0.6, 0.1),
            "Angry": (-0.7, 0.7),
            "Fear": (-0.7, 0.75),
            "Disgusted": (-0.6, 0.6),
            "Surprised": (-0.1, 0.8),
            "Neutral": (-0.3, 0.2),
        },
        "Surprised": {
            "Happy": (0.7, 0.8),
            "Sad": (-0.2, 0.2),
            "Angry": (-0.2, 0.9),
            "Fear": (-0.2, 0.9),
            "Disgusted": (-0.1, 0.8),
            "Surprised": (0.4, 0.9),
            "Neutral": (0.2, 0.4),
        },
        "Neutral": {
            "Happy": (0.4, 0.3),
            "Sad": (-0.35, -0.25),
            "Angry": (-0.4, 0.4),
            "Fear": (-0.2, 0.5),
            "Disgusted": (-0.3, 0.2),
            "Surprised": (0.2, 0.4),
            "Neutral": (0.0, 0.0),
        },
    }
    return labels, table


def build_dataset_full() -> tuple[np.ndarray, np.ndarray, list[str]]:
    labels, table = full49_table_native()
    base = {k: np.array(table[k][k], dtype=float) for k in labels}
    X = []
    y = []
    pairs = []
    for f in labels:
        for v in labels:
            F = base[f]
            V = base[v]
            E = np.array(table[f][v], dtype=float)
            X.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
            y.append([float(E[0]), float(E[1])])
            pairs.append(f"{f}|{v}")
    return np.array(X, dtype=float), np.array(y, dtype=float), pairs


def load_nrc_term_va(path: str, terms: list[str], strict: bool = True) -> dict[str, tuple[float, float]]:
    wanted = {t.lower() for t in terms}
    found: dict[str, tuple[float, float]] = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n").split("\t")
        if len(header) < 3 or header[0] != "term":
            raise ValueError("Unexpected NRC VAD header")
        for raw in f:
            parts = raw.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            term = parts[0].lower()
            if term not in wanted or term in found:
                continue
            v = float(parts[1])
            a = float(parts[2])
            found[term] = (v, a)
            if len(found) == len(wanted):
                break
    missing = [t for t in wanted if t not in found]
    if strict and missing:
        raise ValueError("Missing NRC terms: " + ", ".join(sorted(missing)))
    return found


def affine_fit(old_xy: np.ndarray, new_xy: np.ndarray) -> np.ndarray:
    if old_xy.shape[0] < 3:
        raise ValueError("Need at least 3 points for affine fit")
    X = np.column_stack([old_xy, np.ones((old_xy.shape[0], 1), dtype=float)])
    M, _, _, _ = np.linalg.lstsq(X, new_xy, rcond=None)
    return M


def affine_apply(M: np.ndarray, xy: np.ndarray) -> np.ndarray:
    X = np.column_stack([xy, np.ones((xy.shape[0], 1), dtype=float)])
    return X @ M


def full49_table_nrc_affine(nrc_path: str) -> tuple[list[str], dict[str, dict[str, tuple[float, float]]]]:
    labels, table = full49_table_native()
    base_old = {k: np.array(table[k][k], dtype=float) for k in labels}

    label_to_term = {
        "Happy": "happy",
        "Sad": "sad",
        "Angry": "angry",
        "Fear": "fear",
        "Disgusted": "disgust",
        "Surprised": "surprise",
        "Neutral": "neutral",
    }
    terms = [label_to_term[l] for l in labels]
    nrc = load_nrc_term_va(nrc_path, terms)
    base_new = {l: np.array(nrc[label_to_term[l]], dtype=float) for l in labels}

    old_xy = np.array([base_old[l] for l in labels], dtype=float)
    new_xy = np.array([base_new[l] for l in labels], dtype=float)
    M = affine_fit(old_xy, new_xy)

    out: dict[str, dict[str, tuple[float, float]]] = {}
    for f in labels:
        out[f] = {}
        for v in labels:
            p = np.array(table[f][v], dtype=float).reshape(1, 2)
            t = affine_apply(M, p)[0]
            out[f][v] = (float(t[0]), float(t[1]))
    for l in labels:
        p = base_new[l]
        out[l][l] = (float(p[0]), float(p[1]))
    return labels, out


def nrc_base7(nrc_path: str) -> dict[str, tuple[float, float]]:
    labels = ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]
    label_to_term = {
        "Happy": "happy",
        "Sad": "sad",
        "Angry": "angry",
        "Fear": "fear",
        "Disgusted": "disgust",
        "Surprised": "surprise",
        "Neutral": "neutral",
    }
    terms = [label_to_term[l] for l in labels]
    nrc = load_nrc_term_va(nrc_path, terms)
    return {l: nrc[label_to_term[l]] for l in labels}


def full49_table_nrc_direct(nrc_path: str) -> tuple[list[str], dict[str, dict[str, tuple[float, float]]]]:
    labels = ["Happy", "Sad", "Disgusted", "Fear", "Angry", "Surprised", "Neutral"]

    label_to_term = {
        "Happy": "happy",
        "Sad": "sad",
        "Angry": "angry",
        "Fear": "fear",
        "Disgusted": "disgust",
        "Surprised": "surprise",
        "Neutral": "neutral",
    }

    output_term_grid: dict[str, dict[str, str]] = {
        "Happy": {
            "Happy": "joyful",
            "Sad": "nostalgic",
            "Disgusted": "amused",
            "Fear": "nervous",
            "Angry": "excited",
            "Surprised": "calm",
            "Neutral": "content",
        },
        "Sad": {
            "Happy": "bittersweet",
            "Sad": "depressed",
            "Disgusted": "disillusioned",
            "Fear": "dreadful",
            "Angry": "grieved",
            "Surprised": "sorrowful",
            "Neutral": "disappointed",
        },
        "Disgusted": {
            "Happy": "smug",
            "Sad": "despondent",
            "Disgusted": "nauseated",
            "Fear": "appalled",
            "Angry": "fed up",
            "Surprised": "grossed out",
            "Neutral": "unimpressed",
        },
        "Fear": {
            "Happy": "anxious",
            "Sad": "hopeless",
            "Disgusted": "horrified",
            "Fear": "petrified",
            "Angry": "terrified",
            "Surprised": "stunned",
            "Neutral": "cautious",
        },
        "Angry": {
            "Happy": "sarcastic",
            "Sad": "frustration",
            "Disgusted": "repulsed",
            "Fear": "hostile",
            "Angry": "furious",
            "Surprised": "shocked",
            "Neutral": "unaffected",
        },
        "Surprised": {
            "Happy": "amazed",
            "Sad": "disturbed",
            "Disgusted": "grossed out",
            "Fear": "alarmed",
            "Angry": "startled",
            "Surprised": "astound",
            "Neutral": "unfazed",
        },
        "Neutral": {
            "Happy": "neutral",
            "Sad": "indifferent",
            "Disgusted": "detached",
            "Fear": "cautious",
            "Angry": "unbothered",
            "Surprised": "unsurprised",
            "Neutral": "impartial",
        },
    }

    needed_terms: set[str] = set(label_to_term.values())
    for f in labels:
        for v in labels:
            needed_terms.add(output_term_grid[f][v])

    aliases = {
        "disillusioned": "disillusionment",
        "repulsed": "repulsion",
        "grossed out": "gross",
        "nauseated": "nausea",
    }
    needed_terms.update(aliases.values())

    def normalize_term(t: str) -> str:
        return " ".join(t.strip().lower().split())

    needed = sorted({normalize_term(t) for t in needed_terms})
    lex = load_nrc_term_va(nrc_path, needed, strict=False)

    def get_va(term: str) -> tuple[float, float]:
        t = normalize_term(term)
        if t in lex:
            return lex[t]
        if t in aliases and aliases[t] in lex:
            return lex[aliases[t]]
        if " " in t:
            parts = [p for p in t.split(" ") if p]
            part_vas = [lex[p] for p in parts if p in lex]
            if part_vas:
                v = float(np.mean([x[0] for x in part_vas]))
                a = float(np.mean([x[1] for x in part_vas]))
                return (v, a)
        raise ValueError("Missing term in NRC lexicon: " + term)

    base = {l: get_va(label_to_term[l]) for l in labels}
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for f in labels:
        out[f] = {}
        for v in labels:
            out[f][v] = get_va(output_term_grid[f][v])
    for l in labels:
        out[l][l] = base[l]
    return labels, out


def cluster(vals: list[float], gap: float) -> list[float]:
    vals = sorted(vals)
    if not vals:
        return []
    clusters: list[list[float]] = []
    cur = [vals[0]]
    for v in vals[1:]:
        if v - cur[-1] > gap:
            clusters.append(cur)
            cur = [v]
        else:
            cur.append(v)
    clusters.append(cur)
    return [sum(c) / len(c) for c in clusters]


def red_box_indices(image_path: str) -> list[tuple[int, int]]:
    img = Image.open(image_path).convert("RGB")
    a = np.array(img)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    mask = (r > 140) & (g < 120) & (b < 120) & ((r - g) > 40) & ((r - b) > 40)

    m = mask.astype(np.uint8)
    for _ in range(3):
        padded = np.pad(m, ((2, 2), (2, 2)), mode="constant", constant_values=0)
        out = np.zeros_like(m)
        for dy in range(5):
            for dx in range(5):
                out = np.maximum(out, padded[dy : dy + m.shape[0], dx : dx + m.shape[1]])
        m = out
    mask = m.astype(bool)

    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []

    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            minx = maxx = x
            miny = maxy = y
            cnt = 0
            while stack:
                cy, cx = stack.pop()
                cnt += 1
                minx = min(minx, cx)
                maxx = max(maxx, cx)
                miny = min(miny, cy)
                maxy = max(maxy, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            bw = maxx - minx + 1
            bh = maxy - miny + 1
            if cnt < 120 or bw < 26 or bh < 18:
                continue
            boxes.append((minx, miny, maxx, maxy, cnt))

    centers = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in boxes]
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    x_centers = cluster(xs, gap=25)
    y_centers = cluster(ys, gap=18)
    x_centers.sort()
    y_centers.sort()

    def nearest_idx(v: float, centers_: list[float]) -> int:
        best_i = 0
        best_d = float("inf")
        for i, c in enumerate(centers_):
            d = abs(v - c)
            if d < best_d:
                best_d = d
                best_i = i
        return best_i

    idxs: set[tuple[int, int]] = set()
    for cx, cy in centers:
        col = nearest_idx(cx, x_centers)
        row = nearest_idx(cy, y_centers)
        idxs.add((row, col))
    return sorted(idxs)

def build_dataset_selected_14() -> tuple[np.ndarray, np.ndarray, list[str]]:
    base = base_emotion_coords()
    selected = [
        ("Happy", "Fear", "Nervous", (-0.6, 0.7)),
        ("Happy", "Angry", "Excited", (0.9, 0.8)),
        ("Sad", "Sad", "Depressed", (-0.8, -0.6)),
        ("Sad", "Neutral", "Disappointed", (-0.6, -0.4)),
        ("Disgusted", "Angry", "Fed up", (-0.7, 0.5)),
        ("Disgusted", "Surprised", "Grossed out", (-0.7, 0.6)),
        ("Fear", "Happy", "Anxious", (-0.6, 0.8)),
        ("Fear", "Disgusted", "Horrified", (-0.9, 0.9)),
        ("Angry", "Happy", "Sarcastic", (0.2, 0.4)),
        ("Angry", "Fear", "Hostile", (-0.8, 0.8)),
        ("Surprised", "Happy", "Amazed", (0.7, 0.9)),
        ("Surprised", "Angry", "Astound", (0.2, 0.9)),
        ("Neutral", "Disgusted", "Detached", (-0.3, 0.1)),
        ("Neutral", "Neutral", "Impartial", (0.0, 0.0)),
    ]

    X = []
    y = []
    names = []
    for f, v, out_name, out_coord in selected:
        F = base[f]
        V = base[v]
        E = np.array(out_coord, dtype=float)
        X.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
        y.append([float(E[0]), float(E[1])])
        names.append(f"{f}|{v}->{out_name}")
    return np.array(X, dtype=float), np.array(y, dtype=float), names


def build_dataset_table14_from_table(
    labels: list[str],
    table: dict[str, dict[str, tuple[float, float]]],
) -> tuple[np.ndarray, np.ndarray, list[str], set[str]]:
    base = {k: np.array(table[k][k], dtype=float) for k in labels}
    pairs = [
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

    X = []
    y = []
    names = []
    train_pairs: set[str] = set()
    for f, v, out_name in pairs:
        if f not in base or v not in base:
            raise ValueError("Unexpected label in table14: " + f + " " + v)
        F = base[f]
        V = base[v]
        E = np.array(table[f][v], dtype=float)
        X.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
        y.append([float(E[0]), float(E[1])])
        pair = f"{f}|{v}"
        train_pairs.add(pair)
        names.append(f"{pair}->{out_name}")
    return np.array(X, dtype=float), np.array(y, dtype=float), names, train_pairs


def build_dataset_red14_from_table(
    labels: list[str],
    table: dict[str, dict[str, tuple[float, float]]],
    image_path: str,
) -> tuple[np.ndarray, np.ndarray, list[str], set[str]]:
    base = {k: np.array(table[k][k], dtype=float) for k in labels}
    idxs = red_box_indices(image_path)
    if len(idxs) != 14:
        raise ValueError(f"Expected 14 red boxes, got {len(idxs)}")

    X = []
    y = []
    names = []
    train_pairs: set[str] = set()
    for (row, col) in idxs:
        f = labels[row]
        v = labels[col]
        F = base[f]
        V = base[v]
        E = np.array(table[f][v], dtype=float)
        X.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
        y.append([float(E[0]), float(E[1])])
        pair = f"{f}|{v}"
        train_pairs.add(pair)
        names.append(pair)
    return np.array(X, dtype=float), np.array(y, dtype=float), names, train_pairs


def z_from_d(d: np.ndarray, a1: float, a2: float, b: float, form: str) -> np.ndarray:
    if form == "avg":
        return np.full_like(d, b)
    if form == "linear":
        return a1 * d + b
    if form == "abs":
        return a1 * d + a2 * np.abs(d) + b
    if form == "quad":
        return a1 * d + a2 * (d * d) + b
    raise ValueError("form must be one of: avg, linear, abs, quad")


def dz_da2(d: np.ndarray, form: str) -> np.ndarray:
    if form == "avg":
        return np.zeros_like(d)
    if form == "linear":
        return np.zeros_like(d)
    if form == "abs":
        return np.abs(d)
    if form == "quad":
        return d * d
    raise ValueError("form must be one of: avg, linear, abs, quad")


def forward(params: np.ndarray, X: np.ndarray, form: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    v_f = X[:, 0]
    a_f = X[:, 1]
    v_v = X[:, 2]
    a_vc = X[:, 3]

    dV = v_v - v_f
    dA = a_vc - a_f

    if form == "avg":
        wV = np.full_like(dV, 0.5, dtype=float)
        wA = np.full_like(dA, 0.5, dtype=float)
        v_out = v_f + wV * dV
        a_out = a_f + wA * dA
        pred = np.column_stack([v_out, a_out])
        return pred, wV, wA

    a1_v, a2_v, b_v, a1_a, a2_a, b_a = [float(p) for p in params]
    zV = z_from_d(dV, a1_v, a2_v, b_v, form=form)
    zA = z_from_d(dA, a1_a, a2_a, b_a, form=form)
    wV = sigmoid(zV)
    wA = sigmoid(zA)

    v_out = v_f + wV * dV
    a_out = a_f + wA * dA

    pred = np.column_stack([v_out, a_out])
    return pred, wV, wA


def loss_and_grad(
    params: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    form: str,
    l2: float,
) -> tuple[float, np.ndarray]:
    pred, wV, wA = forward(params, X, form=form)
    err = pred - y
    n = float(len(X))
    loss = float(np.mean(np.sum(err * err, axis=1)))

    dV = X[:, 2] - X[:, 0]
    dA = X[:, 3] - X[:, 1]

    sV = wV * (1.0 - wV)
    sA = wA * (1.0 - wA)

    dL_dv = (2.0 / n) * err[:, 0]
    dL_da = (2.0 / n) * err[:, 1]

    dL_dzV = dL_dv * (sV * dV)
    dL_dzA = dL_da * (sA * dA)

    g_a1_v = float(np.sum(dL_dzV * dV))
    g_a2_v = float(np.sum(dL_dzV * dz_da2(dV, form=form)))
    g_b_v = float(np.sum(dL_dzV))

    g_a1_a = float(np.sum(dL_dzA * dA))
    g_a2_a = float(np.sum(dL_dzA * dz_da2(dA, form=form)))
    g_b_a = float(np.sum(dL_dzA))

    if l2 > 0:
        a1_v, a2_v, _, a1_a, a2_a, _ = [float(p) for p in params]
        loss = float(loss + l2 * (a1_v * a1_v + a2_v * a2_v + a1_a * a1_a + a2_a * a2_a))
        g_a1_v += 2.0 * l2 * a1_v
        g_a2_v += 2.0 * l2 * a2_v
        g_a1_a += 2.0 * l2 * a1_a
        g_a2_a += 2.0 * l2 * a2_a

    return loss, np.array([g_a1_v, g_a2_v, g_b_v, g_a1_a, g_a2_a, g_b_a], dtype=float)


def transform_params(
    raw_params: np.ndarray,
    constraint: str,
    b_sign: str = "free",
) -> tuple[np.ndarray, np.ndarray]:
    raw_params = np.array(raw_params, dtype=float)
    a1_v_raw, a2_v, b_v, a1_a_raw, a2_a, b_a = [float(p) for p in raw_params]

    if constraint == "A":
        a1_v = a1_v_raw
        a1_a = a1_a_raw
        da1_v = 1.0
        da1_a = 1.0
    elif constraint == "B":
        a1_v = float(softplus(np.array(a1_v_raw))) + 1e-6
        a1_a = float(softplus(np.array(a1_a_raw))) + 1e-6
        da1_v = float(sigmoid(np.array(a1_v_raw)))
        da1_a = float(sigmoid(np.array(a1_a_raw)))
    elif constraint == "C":
        a1_v = -(float(softplus(np.array(a1_v_raw))) + 1e-6)
        a1_a = -(float(softplus(np.array(a1_a_raw))) + 1e-6)
        da1_v = -float(sigmoid(np.array(a1_v_raw)))
        da1_a = -float(sigmoid(np.array(a1_a_raw)))
    else:
        raise ValueError("constraint must be one of: A, B, C")

    b_v, db_v = transform_sign(b_v, b_sign, eps=0.0)
    b_a, db_a = transform_sign(b_a, b_sign, eps=0.0)

    params = np.array([a1_v, a2_v, b_v, a1_a, a2_a, b_a], dtype=float)
    chain = np.array([da1_v, 1.0, db_v, da1_a, 1.0, db_a], dtype=float)
    return params, chain


def loss_and_grad_raw(
    raw_params: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    form: str,
    constraint: str,
    b_sign: str,
    l2: float,
) -> tuple[float, np.ndarray]:
    params, chain = transform_params(raw_params, constraint=constraint, b_sign=b_sign)
    l, g = loss_and_grad(params, X, y, form=form, l2=l2)
    return l, g * chain


def train_adam(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    steps: int,
    lr: float,
    form: str,
    constraint: str,
    b_sign: str,
    l2: float,
) -> dict:
    rng = random.Random(seed)
    raw_params = np.array(
        [
            rng.uniform(-1.0, 1.0),
            rng.uniform(-1.0, 1.0),
            rng.uniform(-0.8, 0.8),
            rng.uniform(-1.0, 1.0),
            rng.uniform(-1.0, 1.0),
            rng.uniform(-0.8, 0.8),
        ],
        dtype=float,
    )

    m = np.zeros_like(raw_params)
    v = np.zeros_like(raw_params)
    beta1 = 0.9
    beta2 = 0.999
    eps = 1e-8

    best_loss = float("inf")
    best_raw = raw_params.copy()

    for t in range(1, steps + 1):
        l, g = loss_and_grad_raw(raw_params, X, y, form=form, constraint=constraint, b_sign=b_sign, l2=l2)
        if l < best_loss:
            best_loss = l
            best_raw = raw_params.copy()
        m = beta1 * m + (1.0 - beta1) * g
        v = beta2 * v + (1.0 - beta2) * (g * g)
        m_hat = m / (1.0 - beta1**t)
        v_hat = v / (1.0 - beta2**t)
        raw_params = raw_params - lr * m_hat / (np.sqrt(v_hat) + eps)

    best_params, _ = transform_params(best_raw, constraint=constraint, b_sign=b_sign)
    return {"seed": seed, "loss": best_loss, "params": best_params}


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - float(np.mean(y_true))) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    err = y_pred - y_true
    return float(np.mean(np.sum(err * err, axis=1)))


def plot_weights(params: np.ndarray, X: np.ndarray, form: str, out_path: str) -> None:
    pred, wV, wA = forward(params, X, form=form)
    dV = X[:, 2] - X[:, 0]
    dA = X[:, 3] - X[:, 1]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(dV, wV, s=40)
    xs = np.linspace(float(np.min(dV)), float(np.max(dV)), 400)
    if form == "avg":
        axes[0].plot(xs, np.full_like(xs, 0.5, dtype=float), color="tab:red")
    else:
        a1_v, a2_v, b_v, _, _, _ = [float(p) for p in params]
        ys = sigmoid(z_from_d(xs, a1_v, a2_v, b_v, form=form))
        axes[0].plot(xs, ys, color="tab:red")
    axes[0].set_title("w_v^V vs dV")
    axes[0].set_xlabel("dV = v_voice - v_face")
    axes[0].set_ylabel("w_v^V")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(dA, wA, s=40)
    xs = np.linspace(float(np.min(dA)), float(np.max(dA)), 400)
    if form == "avg":
        axes[1].plot(xs, np.full_like(xs, 0.5, dtype=float), color="tab:red")
    else:
        _, _, _, a1_a, a2_a, b_a = [float(p) for p in params]
        ys = sigmoid(z_from_d(xs, a1_a, a2_a, b_a, form=form))
        axes[1].plot(xs, ys, color="tab:red")
    axes[1].set_title("w_v^A vs dA")
    axes[1].set_xlabel("dA = a_voice - a_face")
    axes[1].set_ylabel("w_v^A")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    _ = pred


def plot_fit_quality(y_true: np.ndarray, y_pred: np.ndarray, out_path: str, title: str) -> None:
    r2_v = r2_score(y_true[:, 0], y_pred[:, 0])
    r2_a = r2_score(y_true[:, 1], y_pred[:, 1])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(y_true[:, 0], y_pred[:, 0], s=45)
    lo = float(min(np.min(y_true[:, 0]), np.min(y_pred[:, 0])))
    hi = float(max(np.max(y_true[:, 0]), np.max(y_pred[:, 0])))
    axes[0].plot([lo, hi], [lo, hi], color="tab:red", linestyle="--")
    axes[0].set_title(f"Valence Fit (R2={r2_v:.3f}) {title}")
    axes[0].set_xlabel("True valence")
    axes[0].set_ylabel("Pred valence")
    axes[0].grid(True, alpha=0.3)

    axes[1].scatter(y_true[:, 1], y_pred[:, 1], s=45)
    lo = float(min(np.min(y_true[:, 1]), np.min(y_pred[:, 1])))
    hi = float(max(np.max(y_true[:, 1]), np.max(y_pred[:, 1])))
    axes[1].plot([lo, hi], [lo, hi], color="tab:red", linestyle="--")
    axes[1].set_title(f"Arousal Fit (R2={r2_a:.3f}) {title}")
    axes[1].set_xlabel("True arousal")
    axes[1].set_ylabel("Pred arousal")
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def plot_error_heatmaps(y_true: np.ndarray, y_pred: np.ndarray, pairs: list[str], out_path: str) -> None:
    labels = ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]
    idx = {k: i for i, k in enumerate(labels)}

    e_v = np.full((len(labels), len(labels)), np.nan, dtype=float)
    e_a = np.full((len(labels), len(labels)), np.nan, dtype=float)
    e_l2 = np.full((len(labels), len(labels)), np.nan, dtype=float)

    for k, pair in enumerate(pairs):
        f, v = pair.split("|", 1)
        i = idx[f]
        j = idx[v]
        dv = float(y_pred[k, 0] - y_true[k, 0])
        da = float(y_pred[k, 1] - y_true[k, 1])
        e_v[i, j] = dv
        e_a[i, j] = da
        e_l2[i, j] = math.sqrt(dv * dv + da * da)

    vmax_v = float(np.nanmax(np.abs(e_v))) if np.any(np.isfinite(e_v)) else 1.0
    vmax_a = float(np.nanmax(np.abs(e_a))) if np.any(np.isfinite(e_a)) else 1.0
    vmax_l2 = float(np.nanmax(e_l2)) if np.any(np.isfinite(e_l2)) else 1.0

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    im0 = axes[0].imshow(e_v, vmin=-vmax_v, vmax=vmax_v, cmap="coolwarm")
    axes[0].set_title("Valence Error (pred - true)")
    axes[0].set_xticks(range(len(labels)))
    axes[0].set_yticks(range(len(labels)))
    axes[0].set_xticklabels(labels, rotation=45, ha="right")
    axes[0].set_yticklabels(labels)
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

    im1 = axes[1].imshow(e_a, vmin=-vmax_a, vmax=vmax_a, cmap="coolwarm")
    axes[1].set_title("Arousal Error (pred - true)")
    axes[1].set_xticks(range(len(labels)))
    axes[1].set_yticks(range(len(labels)))
    axes[1].set_xticklabels(labels, rotation=45, ha="right")
    axes[1].set_yticklabels(labels)
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

    im2 = axes[2].imshow(e_l2, vmin=0, vmax=vmax_l2, cmap="magma")
    axes[2].set_title("VA Error Magnitude (L2)")
    axes[2].set_xticks(range(len(labels)))
    axes[2].set_yticks(range(len(labels)))
    axes[2].set_xticklabels(labels, rotation=45, ha="right")
    axes[2].set_yticklabels(labels)
    fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)

    for ax in axes:
        ax.set_xlabel("V emotion")
        ax.set_ylabel("F emotion")

    plt.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def format_pred_table(pairs: list[str], y_pred: np.ndarray, decimals: int = 2) -> str:
    labels = ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]
    idx = {k: i for i, k in enumerate(labels)}
    grid: list[list[str]] = [["" for _ in labels] for _ in labels]
    for k, pair in enumerate(pairs):
        f, v = pair.split("|", 1)
        i = idx[f]
        j = idx[v]
        vv = round(float(y_pred[k, 0]), decimals)
        aa = round(float(y_pred[k, 1]), decimals)
        grid[i][j] = f"({vv},{aa})"

    header = ",".join(["F\\V", *labels])
    lines = [header]
    for i, f in enumerate(labels):
        lines.append(",".join([f, *grid[i]]))
    return "\n".join(lines)


def run_experiment(
    dataset: str,
    form: str,
    constraint: str,
    b_sign: str,
    coord: str,
    nrc_path: str,
    image_path: str,
    eval_full: bool,
    steps: int,
    lr: float,
    l2: float,
    tag_override: str | None = None,
    out_dir: str = ".",
) -> dict:
    if coord == "native":
        labels, table = full49_table_native()
    elif coord == "nrc_affine":
        labels, table = full49_table_nrc_affine(nrc_path=nrc_path)
    elif coord == "nrc_direct":
        labels, table = full49_table_nrc_direct(nrc_path=nrc_path)
    else:
        raise ValueError("coord must be one of: native, nrc_affine, nrc_direct")

    if dataset == "selected":
        X, y, names = build_dataset_selected_14()
        ds_name = "selected14"
        train_pairs = None
    elif dataset == "table14":
        X, y, names, train_pairs = build_dataset_table14_from_table(labels=labels, table=table)
        ds_name = "table14"
    elif dataset == "red14":
        X, y, names, train_pairs = build_dataset_red14_from_table(labels=labels, table=table, image_path=image_path)
        ds_name = "red14"
    else:
        X, y, names = build_dataset_full()
        ds_name = "full49"
        train_pairs = None

    if form == "avg":
        params = np.zeros((6,), dtype=float)
        pred_train, _, _ = forward(params, X, form=form)
        train_mse = float(mse(y, pred_train))
        train_r2_v = r2_score(y[:, 0], pred_train[:, 0])
        train_r2_a = r2_score(y[:, 1], pred_train[:, 1])
        best = {"seed": -1}
    else:
        trials = []
        for seed in [0, 1, 2, 3, 4, 5, 6, 7]:
            trials.append(
                train_adam(
                    X,
                    y,
                    seed=seed,
                    steps=steps,
                    lr=lr,
                    form=form,
                    constraint=constraint,
                    b_sign=b_sign,
                    l2=l2,
                )
            )
        trials.sort(key=lambda d: d["loss"])
        best = trials[0]
        params = np.array(best["params"], dtype=float)
        if form == "linear":
            params[1] = 0.0
            params[4] = 0.0

        pred_train, _, _ = forward(params, X, form=form)
        train_mse = float(best["loss"])
        train_r2_v = r2_score(y[:, 0], pred_train[:, 0])
        train_r2_a = r2_score(y[:, 1], pred_train[:, 1])

    os.makedirs(out_dir, exist_ok=True)
    tag = tag_override if tag_override is not None else f"{ds_name}_{coord}_{form}_{constraint}_b{b_sign}"
    plot_weights(params, X, form=form, out_path=os.path.join(out_dir, f"weights_{tag}.png"))
    plot_fit_quality(y, pred_train, out_path=os.path.join(out_dir, f"fit_{tag}.png"), title=f"({tag})")

    if dataset in ("selected", "red14"):
        with open(os.path.join(out_dir, f"samples_{tag}.txt"), "w", encoding="utf-8") as f:
            for n in names:
                f.write(n + "\n")

    metrics = {
        "dataset": ds_name,
        "form": form,
        "constraint": constraint,
        "b_sign": b_sign,
        "tag": tag,
        "train_mse": train_mse,
        "train_r2_v": float(train_r2_v),
        "train_r2_a": float(train_r2_a),
        "params": [float(x) for x in params],
        "best_seed": int(best["seed"]),
        "weights_plot": os.path.join(out_dir, f"weights_{tag}.png"),
        "fit_plot": os.path.join(out_dir, f"fit_{tag}.png"),
    }

    if eval_full:
        base = {k: np.array(table[k][k], dtype=float) for k in labels}
        X_full = []
        y_full = []
        pairs_full = []
        for f in labels:
            for v in labels:
                F = base[f]
                V = base[v]
                E = np.array(table[f][v], dtype=float)
                X_full.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
                y_full.append([float(E[0]), float(E[1])])
                pairs_full.append(f"{f}|{v}")
        X_full = np.array(X_full, dtype=float)
        y_full = np.array(y_full, dtype=float)
        pred_full, _, _ = forward(params, X_full, form=form)
        metrics.update(
            {
                "eval_mse": float(mse(y_full, pred_full)),
                "eval_r2_v": float(r2_score(y_full[:, 0], pred_full[:, 0])),
                "eval_r2_a": float(r2_score(y_full[:, 1], pred_full[:, 1])),
            }
        )
        plot_fit_quality(y_full, pred_full, out_path=os.path.join(out_dir, f"eval_fit_{tag}.png"), title=f"(eval {tag})")
        plot_error_heatmaps(y_full, pred_full, pairs_full, out_path=os.path.join(out_dir, f"eval_err_{tag}.png"))
        metrics["eval_fit_plot"] = os.path.join(out_dir, f"eval_fit_{tag}.png")
        metrics["eval_err_plot"] = os.path.join(out_dir, f"eval_err_{tag}.png")

        if train_pairs is not None:
            keep = [i for i, p in enumerate(pairs_full) if p not in train_pairs]
            X_ho = X_full[keep]
            y_ho = y_full[keep]
            pairs_ho = [pairs_full[i] for i in keep]
            pred_ho, _, _ = forward(params, X_ho, form=form)
            metrics["holdout35_mse"] = float(mse(y_ho, pred_ho))
            metrics["holdout35_r2_v"] = float(r2_score(y_ho[:, 0], pred_ho[:, 0]))
            metrics["holdout35_r2_a"] = float(r2_score(y_ho[:, 1], pred_ho[:, 1]))
            plot_fit_quality(
                y_ho,
                pred_ho,
                out_path=os.path.join(out_dir, f"holdout_fit_{tag}.png"),
                title=f"(holdout35 {tag})",
            )
            plot_error_heatmaps(
                y_ho,
                pred_ho,
                pairs_ho,
                out_path=os.path.join(out_dir, f"holdout_err_{tag}.png"),
            )
            metrics["holdout_fit_plot"] = os.path.join(out_dir, f"holdout_fit_{tag}.png")
            metrics["holdout_err_plot"] = os.path.join(out_dir, f"holdout_err_{tag}.png")

    a1_v, a2_v, b_v, a1_a, a2_a, b_a = metrics["params"]
    print(f"\n{tag}")
    print("params:")
    print(f"a1_v={a1_v} a2_v={a2_v} b_v={b_v}")
    print(f"a1_a={a1_a} a2_a={a2_a} b_a={b_a}")
    print("train:")
    print(f"mse={metrics['train_mse']} r2_v={metrics['train_r2_v']} r2_a={metrics['train_r2_a']} seed={metrics['best_seed']}")
    if eval_full:
        print("eval_full:")
        print(f"mse={metrics['eval_mse']} r2_v={metrics['eval_r2_v']} r2_a={metrics['eval_r2_a']}")
        if "holdout35_mse" in metrics:
            print("holdout35:")
            print(f"mse={metrics['holdout35_mse']} r2_v={metrics['holdout35_r2_v']} r2_a={metrics['holdout35_r2_a']}")

    return metrics


def plot_comparison(results: list[dict], out_path: str) -> None:
    keys = ["train_mse", "eval_mse", "eval_r2_v", "eval_r2_a"]
    fig, axes = plt.subplots(1, len(keys), figsize=(18, 4))
    for ax, key in zip(axes, keys):
        vals = [r.get(key, float("nan")) for r in results]
        ax.bar([r.get("tag", r["constraint"]) for r in results], vals)
        ax.set_title(key)
        ax.tick_params(axis="x", labelrotation=35)
        ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def monotonicity_over_range(d_min: float, d_max: float, a1: float, a2: float) -> tuple[bool, float | None]:
    if abs(a2) < 1e-12:
        return True, None
    g0 = a1 + 2.0 * a2 * d_min
    g1 = a1 + 2.0 * a2 * d_max
    is_mono = (g0 == 0.0) or (g1 == 0.0) or (g0 * g1 > 0.0)
    d_star = -a1 / (2.0 * a2)
    if d_star < d_min or d_star > d_max:
        return True, None
    return is_mono, d_star


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["selected", "table14", "full", "red14"], default="selected")
    parser.add_argument("--form", choices=["avg", "linear", "abs", "quad", "both"], default="both")
    parser.add_argument("--constraint", choices=["A", "B", "C", "all"], default="all")
    parser.add_argument("--b-sign", choices=["free", "pos", "neg"], default="free")
    parser.add_argument("--cases4", action="store_true")
    parser.add_argument("--eval-full", action="store_true")
    parser.add_argument("--dump-table", action="store_true")
    parser.add_argument("--coord", choices=["native", "nrc_affine", "nrc_direct"], default="native")
    parser.add_argument("--nrc-path", default="NRC-VAD-Lexicon-v2.1.txt")
    parser.add_argument("--image-path", default="image.png")
    parser.add_argument("--out-dir", default=".")
    parser.add_argument("--steps", type=int, default=8000)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=0.0)
    args = parser.parse_args()

    if args.coord in ("nrc_affine", "nrc_direct"):
        os.makedirs(args.out_dir, exist_ok=True)
        base7 = nrc_base7(args.nrc_path)
        out_lines = []
        for k in ["Happy", "Sad", "Angry", "Fear", "Disgusted", "Surprised", "Neutral"]:
            v, a = base7[k]
            out_lines.append(f"{k}\tvalence={v}\tarousal={a}")
        with open(os.path.join(args.out_dir, "nrc_base7.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")

    forms = ["linear", "abs", "quad"] if args.form == "both" else [args.form]
    constraints = ["A", "B", "C"] if args.constraint == "all" else [args.constraint]

    for form in forms:
        results = []
        if form == "avg":
            results.append(
                run_experiment(
                    dataset=args.dataset,
                    form=form,
                    constraint="A",
                    b_sign="free",
                    coord=args.coord,
                    nrc_path=args.nrc_path,
                    image_path=args.image_path,
                    eval_full=args.eval_full,
                    steps=args.steps,
                    lr=args.lr,
                    l2=args.l2,
                    tag_override=f"{args.dataset}_{args.coord}_{form}",
                    out_dir=args.out_dir,
                )
            )
        elif args.cases4:
            cases = [
                ("B", "pos", "ap_bp"),
                ("B", "neg", "ap_bn"),
                ("C", "pos", "an_bp"),
                ("C", "neg", "an_bn"),
            ]
            for a1_constraint, b_sign, tag in cases:
                results.append(
                    run_experiment(
                        dataset=args.dataset,
                        form=form,
                        constraint=a1_constraint,
                        b_sign=b_sign,
                        coord=args.coord,
                        nrc_path=args.nrc_path,
                        image_path=args.image_path,
                        eval_full=args.eval_full,
                        steps=args.steps,
                        lr=args.lr,
                        l2=args.l2,
                        tag_override=f"{args.dataset}_{args.coord}_{form}_{tag}",
                        out_dir=args.out_dir,
                    )
                )
        else:
            for c in constraints:
                results.append(
                    run_experiment(
                        dataset=args.dataset,
                        form=form,
                        constraint=c,
                        b_sign=args.b_sign,
                        coord=args.coord,
                        nrc_path=args.nrc_path,
                        image_path=args.image_path,
                        eval_full=args.eval_full,
                        steps=args.steps,
                        lr=args.lr,
                        l2=args.l2,
                        out_dir=args.out_dir,
                    )
                )

        if form == "quad":
            X_full, _, _ = build_dataset_full()
            dV = X_full[:, 2] - X_full[:, 0]
            dA = X_full[:, 3] - X_full[:, 1]
            dv_min, dv_max = float(np.min(dV)), float(np.max(dV))
            da_min, da_max = float(np.min(dA)), float(np.max(dA))
            for r in results:
                a1_v, a2_v, b_v, a1_a, a2_a, b_a = r["params"]
                mv, dv_star = monotonicity_over_range(dv_min, dv_max, a1=float(a1_v), a2=float(a2_v))
                ma, da_star = monotonicity_over_range(da_min, da_max, a1=float(a1_a), a2=float(a2_a))
                r["mono_v"] = bool(mv)
                r["mono_a"] = bool(ma)
                r["turn_v"] = dv_star
                r["turn_a"] = da_star
                print(f"monotonicity ({r.get('tag', '')}): V={'mono' if mv else 'non-mono'} A={'mono' if ma else 'non-mono'}")
                if dv_star is not None:
                    w_star = float(sigmoid(z_from_d(np.array([dv_star]), float(a1_v), float(a2_v), float(b_v), form="quad"))[0])
                    print(f"turning point V d*={dv_star} w(d*)={w_star}")
                if da_star is not None:
                    w_star = float(sigmoid(z_from_d(np.array([da_star]), float(a1_a), float(a2_a), float(b_a), form="quad"))[0])
                    print(f"turning point A d*={da_star} w(d*)={w_star}")

        if len(results) > 1:
            ds_name = results[0]["dataset"]
            out_name = f"compare_{ds_name}_{form}.png" if not args.cases4 else f"compare_{ds_name}_{form}_cases4.png"
            plot_comparison(results, out_path=os.path.join(args.out_dir, out_name))
            print("saved " + out_name)

        if args.dump_table:
            if args.coord == "native":
                labels, table = full49_table_native()
            elif args.coord == "nrc_affine":
                labels, table = full49_table_nrc_affine(args.nrc_path)
            elif args.coord == "nrc_direct":
                labels, table = full49_table_nrc_direct(args.nrc_path)
            else:
                raise ValueError("coord must be one of: native, nrc_affine, nrc_direct")
            base = {k: np.array(table[k][k], dtype=float) for k in labels}
            X_full = []
            pairs_full = []
            for f in labels:
                for v in labels:
                    F = base[f]
                    V = base[v]
                    X_full.append([float(F[0]), float(F[1]), float(V[0]), float(V[1])])
                    pairs_full.append(f"{f}|{v}")
            X_full = np.array(X_full, dtype=float)
            os.makedirs(args.out_dir, exist_ok=True)
            for r in results:
                pred_full, _, _ = forward(np.array(r["params"], dtype=float), X_full, form=form)
                table_csv = format_pred_table(pairs_full, pred_full, decimals=2)
                print("\nPRED_TABLE_CSV")
                print(table_csv)
                with open(os.path.join(args.out_dir, f"pred_table_{r.get('tag', 'run')}.csv"), "w", encoding="utf-8") as f:
                    f.write(table_csv + "\n")


if __name__ == "__main__":
    main()
