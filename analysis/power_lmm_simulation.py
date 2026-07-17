"""Monte Carlo power for the prespecified A2 PI-minus-LI paired model."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from run_analysis import build_distance_contrasts, run_primary_model


CONCEPTS = ("JOY", "AMUSEMENT", "TENDERNESS", "ANGER", "SADNESS", "FEAR")


def parse_sizes(value: str) -> list[int]:
    sizes = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not sizes or any(size < 10 for size in sizes):
        raise argparse.ArgumentTypeError("sample sizes must be comma-separated integers >= 10")
    return sizes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-sizes", type=parse_sizes, default=parse_sizes("30,36,42,48"))
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--effect", type=float, default=-0.20)
    parser.add_argument("--participant-intercept-sd", type=float, default=0.17)
    parser.add_argument("--participant-slope-sd", type=float, default=0.15)
    parser.add_argument("--intercept-slope-correlation", type=float, default=-0.20)
    parser.add_argument("--concept-slope-sd", type=float, default=0.08)
    parser.add_argument("--residual-sd", type=float, default=0.58)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.iterations < 1:
        raise ValueError("iterations must be positive")
    if not -0.99 < args.intercept_slope_correlation < 0.99:
        raise ValueError("correlation must be between -0.99 and 0.99")
    if any(value < 0 for value in (
        args.participant_intercept_sd, args.participant_slope_sd,
        args.concept_slope_sd, args.residual_sd,
    )):
        raise ValueError("standard deviations must be nonnegative")
    if not 0 < args.alpha < 1:
        raise ValueError("alpha must be in (0, 1)")


def simulate_distances(n: int, args: argparse.Namespace, rng: np.random.Generator) -> pd.DataFrame:
    covariance = np.array([
        [args.participant_intercept_sd ** 2,
         args.intercept_slope_correlation * args.participant_intercept_sd * args.participant_slope_sd],
        [args.intercept_slope_correlation * args.participant_intercept_sd * args.participant_slope_sd,
         args.participant_slope_sd ** 2],
    ])
    participant_effects = rng.multivariate_normal([0, 0], covariance, size=n)
    raw_concept_slopes = rng.normal(0, args.concept_slope_sd, size=len(CONCEPTS))
    concept_slopes = raw_concept_slopes - raw_concept_slopes.mean()
    concept_intercepts = np.linspace(-0.12, 0.12, len(CONCEPTS))
    rows = []
    for participant_index in range(n):
        participant_id = f"P{participant_index + 1:03d}"
        session_order = 1 if participant_index % 2 == 0 else 2
        prototype_first = participant_index % 4 in (1, 2)
        block_by_source = {
            "prototype": 1 if prototype_first else 2,
            "lexical": 2 if prototype_first else 1,
        }
        random_intercept, random_slope = participant_effects[participant_index]
        for concept_index, concept_id in enumerate(CONCEPTS):
            for source in ("lexical", "prototype"):
                source_prototype = int(source == "prototype")
                mean = (
                    1.40 + concept_intercepts[concept_index] + random_intercept
                    + source_prototype * (
                        args.effect + concept_slopes[concept_index] + random_slope
                    )
                )
                rows.append({
                    "participant_id": participant_id,
                    "concept_id": concept_id,
                    "source": source,
                    "session_order": session_order,
                    "block_order": block_by_source[source],
                    "distance": rng.normal(mean, args.residual_sd),
                })
    return pd.DataFrame(rows)


def run_condition(n: int, args: argparse.Namespace, seed: np.random.SeedSequence) -> dict[str, object]:
    child_seeds = seed.spawn(args.iterations)
    estimates = []
    standard_errors = []
    significant_in_direction = 0
    fit_failures = 0
    paths: Counter[str] = Counter()
    for child_seed in child_seeds:
        rng = np.random.default_rng(child_seed)
        try:
            contrasts = build_distance_contrasts(simulate_distances(n, args, rng))
            result = run_primary_model(contrasts)
            estimate = float(result.params["Intercept"])
            p_value = float(result.pvalues["Intercept"])
            standard_error = float(result.bse["Intercept"])
            estimates.append(estimate)
            standard_errors.append(standard_error)
            significant_in_direction += int(p_value < args.alpha and estimate < 0)
            paths[result.a2_model_path] += 1
        except Exception:
            fit_failures += 1
    successful = len(estimates)
    return {
        "complete_n": n,
        "iterations_requested": args.iterations,
        "successful_fits": successful,
        "fit_failures": fit_failures,
        "power_directional_at_two_sided_alpha": (
            round(significant_in_direction / successful, 4) if successful else math.nan
        ),
        "mean_estimate": round(float(np.mean(estimates)), 4) if estimates else math.nan,
        "mean_standard_error": round(float(np.mean(standard_errors)), 4) if standard_errors else math.nan,
        "model_paths": json.dumps(paths, ensure_ascii=False, sort_keys=True),
    }


def main() -> None:
    args = parse_args()
    validate_args(args)
    root_seed = np.random.SeedSequence(args.seed)
    condition_seeds = root_seed.spawn(len(args.sample_sizes))
    rows = [
        run_condition(n, args, condition_seed)
        for n, condition_seed in zip(args.sample_sizes, condition_seeds)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(
        f"PASS conditions={len(rows)} iterations={args.iterations} "
        f"effect={args.effect} output={args.output.name}"
    )


if __name__ == "__main__":
    main()
