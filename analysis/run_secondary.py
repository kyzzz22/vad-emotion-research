"""Prespecified secondary dimension-consistency analysis for A2."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from run_analysis import DIMENSIONS, validate_ratings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def build_dimension_differences(data: pd.DataFrame) -> pd.DataFrame:
    covariates = data.loc[
        data["condition"].isin(["lexical", "prototype"]),
        ["participant_id", "concept_id", "condition", "session_order", "block_order"],
    ].rename(columns={"condition": "source"})
    long = data.melt(
        id_vars=["participant_id", "concept_id", "condition", "session_order"],
        value_vars=DIMENSIONS, var_name="dimension", value_name="score",
    )
    pooled = long.groupby("dimension")["score"].agg(["mean", "std"])
    long = long.join(pooled, on="dimension")
    long["z_score"] = (long["score"] - long["mean"]) / long["std"]
    wide = long.pivot_table(
        index=["participant_id", "concept_id", "session_order"],
        columns=["condition", "dimension"], values="z_score", aggfunc="mean",
    )
    rows = []
    for source in ("lexical", "prototype"):
        for dimension in DIMENSIONS:
            signed = wide[("induced", dimension)] - wide[(source, dimension)]
            frame = signed.rename("signed_difference").reset_index()
            frame["absolute_difference"] = frame["signed_difference"].abs()
            frame["source"] = source
            frame["dimension"] = dimension
            frame = frame.merge(
                covariates, on=["participant_id", "concept_id", "source", "session_order"],
                how="left", validate="one_to_one",
            )
            rows.append(frame)
    return pd.concat(rows, ignore_index=True).dropna(subset=["absolute_difference"])


def tidy(result) -> pd.DataFrame:
    confidence = result.conf_int()
    rows = []
    dimension_terms = []
    for term in result.params.index:
        if term.startswith("C(dimension"):
            dimension_terms.append(term)
        rows.append({
            "term": term,
            "estimate": float(result.params[term]),
            "standard_error": float(result.bse[term]),
            "statistic": float(result.tvalues[term]),
            "p_value": float(result.pvalues[term]),
            "ci_low": float(confidence.loc[term].iloc[0]),
            "ci_high": float(confidence.loc[term].iloc[1]),
            "holm_p_value_dimension_family": np.nan,
        })
    output = pd.DataFrame(rows)
    if dimension_terms:
        adjusted = multipletests(
            [float(result.pvalues[term]) for term in dimension_terms], method="holm"
        )[1]
        for term, p_value in zip(dimension_terms, adjusted):
            output.loc[output["term"].eq(term), "holm_p_value_dimension_family"] = p_value
    return output


def main() -> None:
    args = parse_args()
    data = pd.read_csv(args.ratings)
    if "subjective_qc" in data.columns:
        data = data.loc[data["subjective_qc"].eq("pass")].copy()
    validate_ratings(data)
    differences = build_dimension_differences(data)
    formula = (
        "absolute_difference ~ C(dimension, Treatment('valence')) + "
        "C(source, Treatment('lexical')) + C(concept_id) + session_order + block_order"
    )
    result = smf.gee(
        formula, groups="participant_id", data=differences,
        cov_struct=sm.cov_struct.Exchangeable(), family=sm.families.Gaussian(),
    ).fit()
    args.output.mkdir(parents=True, exist_ok=True)
    differences.to_csv(args.output / "dimension_differences_standardized.csv", index=False)
    tidy(result).to_csv(args.output / "dimension_consistency_effects.csv", index=False)
    differences.groupby(["source", "dimension"], as_index=False).agg(
        n=("absolute_difference", "size"),
        absolute_mean=("absolute_difference", "mean"),
        absolute_sd=("absolute_difference", "std"),
        signed_mean=("signed_difference", "mean"),
        signed_sd=("signed_difference", "std"),
    ).to_csv(args.output / "dimension_consistency_summary.csv", index=False)
    (args.output / "dimension_consistency_model.txt").write_text(
        str(result.summary()), encoding="utf-8"
    )
    print(
        f"PASS participants={differences['participant_id'].nunique()} "
        f"rows={len(differences)} output={args.output.name}"
    )


if __name__ == "__main__":
    main()
