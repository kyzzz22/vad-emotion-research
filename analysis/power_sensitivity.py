"""Exact paired-t sensitivity analysis for the participant-level A2 contrast."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from scipy.stats import nct, t


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "results" / "power_sensitivity.csv"


def paired_t_power(n: int, dz: float, alpha: float = 0.05) -> float:
    df = n - 1
    critical = t.ppf(1 - alpha / 2, df)
    noncentrality = dz * math.sqrt(n)
    return float(nct.cdf(-critical, df, noncentrality) + 1 - nct.cdf(critical, df, noncentrality))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--attrition", type=float, default=0.15)
    args = parser.parse_args()
    if not 0 <= args.attrition < 1:
        raise ValueError("attrition must be in [0, 1)")

    effect_sizes = (0.30, 0.40, 0.50, 0.60)
    sample_sizes = (24, 30, 36, 42, 48, 54, 60, 72, 90)
    rows = []
    for dz in effect_sizes:
        powers = {n: paired_t_power(n, dz) for n in sample_sizes}
        target_n = next((n for n in range(10, 501) if paired_t_power(n, dz) >= 0.80), None)
        rows.append({
            "effect_dz": dz,
            **{f"power_n{n}": round(power, 4) for n, power in powers.items()},
            "complete_n_for_80pct": target_n,
            "recruit_n_with_attrition": math.ceil(target_n / (1 - args.attrition)),
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS rows={len(rows)} output={args.output.name}")


if __name__ == "__main__":
    main()
