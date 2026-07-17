"""Primary analysis for aligned lexical, prototype, and induced VAD ratings."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tools.sm_exceptions import ConvergenceWarning


DIMENSIONS = ["valence", "arousal", "dominance"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def validate_ratings(data: pd.DataFrame) -> None:
    required = {
        "participant_id", "concept_id", "condition", "session_order",
        "block_order", *DIMENSIONS,
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if not data["condition"].isin({"lexical", "prototype", "induced"}).all():
        raise ValueError("Unexpected condition value")
    for dimension in DIMENSIONS:
        if not data[dimension].between(1, 9).all():
            raise ValueError(f"{dimension} contains scores outside 1-9")


def keep_target_concepts(data: pd.DataFrame) -> pd.DataFrame:
    concepts_path = Path(__file__).resolve().parents[1] / "materials" / "emotion_concepts.csv"
    target_ids = set(pd.read_csv(concepts_path)["concept_id"])
    unknown_nonfillers = set(data["concept_id"]) - target_ids
    if unknown_nonfillers:
        raise ValueError(
            "Analysis input contains non-target concepts; run prepare_ratings.py first: "
            f"{sorted(unknown_nonfillers)}"
        )
    return data.copy()


def build_distances(data: pd.DataFrame) -> pd.DataFrame:
    source_covariates = data.loc[
        data["condition"].isin(["lexical", "prototype"]),
        ["participant_id", "concept_id", "condition", "block_order"],
    ].rename(columns={"condition": "source"})
    long = data.melt(
        id_vars=["participant_id", "concept_id", "condition", "session_order", "block_order"],
        value_vars=DIMENSIONS,
        var_name="dimension",
        value_name="score",
    )
    pooled = long.groupby("dimension")["score"].agg(["mean", "std"])
    long = long.join(pooled, on="dimension")
    long["z_score"] = (long["score"] - long["mean"]) / long["std"]

    wide = long.pivot_table(
        index=["participant_id", "concept_id", "session_order"],
        columns=["condition", "dimension"],
        values="z_score",
        aggfunc="mean",
    )
    rows = []
    for source in ("lexical", "prototype"):
        squared = sum(
            (wide[(source, dimension)] - wide[("induced", dimension)]) ** 2
            for dimension in DIMENSIONS
        )
        frame = np.sqrt(squared).rename("distance").reset_index()
        frame["source"] = source
        frame = frame.merge(
            source_covariates,
            on=["participant_id", "concept_id", "source"],
            how="left",
            validate="one_to_one",
        )
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def build_distance_contrasts(distances: pd.DataFrame) -> pd.DataFrame:
    """Create the exact participant-by-concept PI-minus-LI paired contrast."""
    key = ["participant_id", "concept_id", "session_order"]
    if distances.duplicated([*key, "source"]).any():
        raise ValueError("Distance rows are not unique within participant, concept, and source")
    distance_wide = distances.pivot(index=key, columns="source", values="distance")
    block_wide = distances.pivot(index=key, columns="source", values="block_order")
    required_sources = {"lexical", "prototype"}
    if not required_sources.issubset(distance_wide.columns):
        raise ValueError("Both lexical and prototype distances are required")
    if distance_wide[list(required_sources)].isna().any().any():
        raise ValueError("Incomplete lexical/prototype distance pair")

    contrasts = distance_wide.reset_index()[key].copy()
    contrasts["distance_lexical_induced"] = distance_wide["lexical"].to_numpy()
    contrasts["distance_prototype_induced"] = distance_wide["prototype"].to_numpy()
    contrasts["distance_difference"] = (
        contrasts["distance_prototype_induced"]
        - contrasts["distance_lexical_induced"]
    )
    contrasts["prototype_first"] = (block_wide["prototype"].to_numpy() == 1).astype(int)
    contrasts["session_order_c"] = contrasts["session_order"] - 1.5
    contrasts["prototype_first_c"] = contrasts["prototype_first"] - 0.5
    return contrasts


def run_primary_model(contrasts: pd.DataFrame):
    formula = (
        "distance_difference ~ C(concept_id, Sum) + "
        "session_order_c + prototype_first_c"
    )
    model = smf.mixedlm(
        formula,
        contrasts,
        groups=contrasts["participant_id"],
        re_formula="1",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        for method in ("lbfgs", "powell"):
            try:
                result = model.fit(method=method, reml=False)
                random_variance = float(result.cov_re.iloc[0, 0])
                if result.converged and random_variance > 1e-8:
                    result.a2_model_path = f"paired-difference participant random-intercept LMM ({method})"
                    return result
            except Exception:
                continue

    result = smf.ols(formula, data=contrasts).fit(
        cov_type="cluster",
        cov_kwds={"groups": contrasts["participant_id"], "use_correction": True},
        use_t=True,
    )
    result.a2_model_path = "paired-difference participant-clustered OLS fallback"
    return result


def run_source_sensitivity_model(distances: pd.DataFrame):
    distances = distances.copy()
    distances["source_prototype"] = (distances["source"] == "prototype").astype(int)
    model = smf.mixedlm(
        "distance ~ source_prototype + C(concept_id) + session_order + block_order",
        distances,
        groups=distances["participant_id"],
        re_formula="~source_prototype",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        for method in ("lbfgs", "powell"):
            try:
                result = model.fit(method=method, reml=False)
                if result.converged:
                    result.a2_model_path = f"participant random intercept+slope LMM ({method})"
                    return result
            except Exception:
                continue

    fallback = smf.mixedlm(
        "distance ~ source_prototype + C(concept_id) + session_order + block_order",
        distances,
        groups=distances["participant_id"],
        re_formula="1",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        warnings.simplefilter("ignore", UserWarning)
        for method in ("lbfgs", "powell"):
            try:
                result = fallback.fit(method=method, reml=False)
                if result.converged:
                    result.a2_model_path = f"participant random-intercept LMM ({method})"
                    return result
            except Exception:
                continue

    gee = smf.gee(
        "distance ~ source_prototype + C(concept_id) + session_order + block_order",
        groups="participant_id",
        data=distances,
        cov_struct=sm.cov_struct.Exchangeable(),
        family=sm.families.Gaussian(),
    )
    result = gee.fit()
    result.a2_model_path = "participant-clustered GEE fallback"
    return result


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(args.ratings)
    if "subjective_qc" in data.columns:
        data = data.loc[data["subjective_qc"] == "pass"].copy()
    if data.empty:
        raise ValueError("No subjective_qc=pass rows remain for analysis")
    validate_ratings(data)
    data = keep_target_concepts(data)

    summary = data.groupby("condition")[DIMENSIONS].agg(["count", "mean", "std"])
    summary.to_csv(args.output / "condition_summary.csv")

    distances = build_distances(data)
    distances.to_csv(args.output / "vad_distances.csv", index=False)
    contrasts = build_distance_contrasts(distances)
    contrasts.to_csv(args.output / "vad_distance_contrasts.csv", index=False)

    result = run_primary_model(contrasts)
    report = f"Model path: {result.a2_model_path}\n\n{result.summary()}"
    (args.output / "primary_model.txt").write_text(report, encoding="utf-8")
    coefficient = "Intercept"
    confidence = result.conf_int().loc[coefficient]
    paired_difference = contrasts.groupby("participant_id")["distance_difference"].mean()
    paired_dz = paired_difference.mean() / paired_difference.std(ddof=1)
    primary_effect = pd.DataFrame([{
        "term": "mean_distance_PI_minus_LI",
        "estimate": float(result.params[coefficient]),
        "standard_error": float(result.bse[coefficient]),
        "statistic": float(result.tvalues[coefficient]),
        "p_value": float(result.pvalues[coefficient]),
        "ci_low": float(confidence.iloc[0]),
        "ci_high": float(confidence.iloc[1]),
        "participant_paired_dz": float(paired_dz),
        "participant_mean_difference": float(paired_difference.mean()),
        "participant_difference_sd": float(paired_difference.std(ddof=1)),
    }])
    primary_effect.to_csv(args.output / "primary_effect.csv", index=False)

    source_result = run_source_sensitivity_model(distances)
    source_report = f"Model path: {source_result.a2_model_path}\n\n{source_result.summary()}"
    (args.output / "source_model_sensitivity.txt").write_text(source_report, encoding="utf-8")
    source_confidence = source_result.conf_int().loc["source_prototype"]
    pd.DataFrame([{
        "term": "source_prototype",
        "estimate": float(source_result.params["source_prototype"]),
        "standard_error": float(source_result.bse["source_prototype"]),
        "statistic": float(source_result.tvalues["source_prototype"]),
        "p_value": float(source_result.pvalues["source_prototype"]),
        "ci_low": float(source_confidence.iloc[0]),
        "ci_high": float(source_confidence.iloc[1]),
        "model_path": source_result.a2_model_path,
    }]).to_csv(args.output / "source_model_sensitivity_effect.csv", index=False)
    metadata = {
        "model_path": result.a2_model_path,
        "analysis_rows": int(len(data)),
        "distance_rows": int(len(distances)),
        "contrast_rows": int(len(contrasts)),
        "participants": int(data["participant_id"].nunique()),
        "concepts": int(data["concept_id"].nunique()),
        "conditions": sorted(data["condition"].unique().tolist()),
    }
    (args.output / "model_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Model path: {result.a2_model_path}")
    print(result.summary())


if __name__ == "__main__":
    main()
