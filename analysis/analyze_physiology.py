"""Exploratory A2 physiology models for induced arousal and prototype discrepancy."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ConvergenceWarning


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--physiology", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def fit_model(formula: str, data: pd.DataFrame):
    model = smf.mixedlm(formula, data, groups=data["participant_id"], re_formula="1")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        for method in ("lbfgs", "powell"):
            try:
                result = model.fit(method=method, reml=False)
                if result.converged:
                    result.a2_model_path = f"participant random-intercept LMM ({method})"
                    return result
            except Exception:
                continue
    gee = smf.gee(
        formula, groups="participant_id", data=data,
        cov_struct=sm.cov_struct.Exchangeable(), family=sm.families.Gaussian(),
    )
    result = gee.fit()
    result.a2_model_path = "participant-clustered GEE fallback"
    return result


def tidy(result, outcome: str) -> pd.DataFrame:
    confidence = result.conf_int()
    rows = []
    for term in result.params.index:
        rows.append({
            "outcome": outcome,
            "term": term,
            "estimate": float(result.params[term]),
            "standard_error": float(result.bse[term]),
            "statistic": float(result.tvalues[term]),
            "p_value": float(result.pvalues[term]),
            "ci_low": float(confidence.loc[term].iloc[0]),
            "ci_high": float(confidence.loc[term].iloc[1]),
            "model_path": result.a2_model_path,
        })
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    ratings = pd.read_csv(args.ratings)
    physiology = pd.read_csv(args.physiology)
    if "subjective_qc" in ratings.columns:
        ratings = ratings.loc[ratings["subjective_qc"].eq("pass")].copy()
    physiology = physiology.loc[physiology["physiology_qc"].eq("pass")].copy()
    induced = ratings.loc[ratings["condition"].eq("induced"), [
        "participant_id", "concept_id", "stimulus_id", "arousal", "session_order"
    ]].rename(columns={"arousal": "induced_arousal"})
    prototype = ratings.loc[ratings["condition"].eq("prototype"), [
        "participant_id", "concept_id", "arousal"
    ]].rename(columns={"arousal": "prototype_arousal"})
    merged = induced.merge(
        prototype, on=["participant_id", "concept_id"], how="inner", validate="many_to_one"
    ).merge(
        physiology, on=["participant_id", "concept_id", "stimulus_id"],
        how="inner", validate="one_to_one",
    )
    if merged["participant_id"].nunique() < 10:
        raise ValueError("Fewer than 10 participants have aligned pass physiology trials")
    merged["delta_pe_arousal"] = merged["induced_arousal"] - merged["prototype_arousal"]
    predictors = "eda_delta_within_z + hr_delta_within_z + prototype_arousal + C(stimulus_id) + session_order"
    models = {
        "induced_arousal": fit_model(f"induced_arousal ~ {predictors}", merged),
        "delta_pe_arousal": fit_model(f"delta_pe_arousal ~ {predictors}", merged),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    pd.concat([tidy(result, outcome) for outcome, result in models.items()], ignore_index=True).to_csv(
        args.output / "physiology_model_effects.csv", index=False
    )
    merged.to_csv(args.output / "aligned_physiology_trials.csv", index=False)
    metadata = {
        "exploratory": True,
        "participants": int(merged["participant_id"].nunique()),
        "trials": int(len(merged)),
        "model_paths": {outcome: result.a2_model_path for outcome, result in models.items()},
    }
    (args.output / "physiology_model_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for outcome, result in models.items():
        (args.output / f"{outcome}_model.txt").write_text(str(result.summary()), encoding="utf-8")
    print(
        f"PASS participants={metadata['participants']} trials={metadata['trials']} "
        f"output={args.output.name}"
    )


if __name__ == "__main__":
    main()
