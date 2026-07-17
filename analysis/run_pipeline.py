"""Run the reproducible A2 analysis pipeline and record provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy
import pandas
import scipy
import statsmodels


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings-raw", type=Path, required=True)
    parser.add_argument("--physiology", type=Path)
    parser.add_argument("--processed-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(script: str, *arguments: object) -> list[str]:
    command = [sys.executable, str(ANALYSIS / script), *(str(argument) for argument in arguments)]
    subprocess.run(command, cwd=ROOT, check=True)
    return command


def main() -> None:
    args = parse_args()
    if not args.ratings_raw.is_file():
        raise FileNotFoundError(args.ratings_raw)
    if args.physiology and not args.physiology.is_file():
        raise FileNotFoundError(args.physiology)
    args.processed_dir.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    ratings_prepared = args.processed_dir / "ratings_prepared.csv"
    ratings_analysis = args.processed_dir / "ratings_analysis.csv"
    commands = []
    commands.append(run(
        "prepare_ratings.py", "--raw", args.ratings_raw, "--output", ratings_prepared
    ))
    commands.append(run(
        "apply_exclusions.py", "--ratings", ratings_prepared,
        "--output", ratings_analysis, "--log", args.output / "participant_exclusions.csv",
    ))
    commands.append(run(
        "run_analysis.py", "--ratings", ratings_analysis, "--output", args.output / "primary"
    ))
    commands.append(run(
        "run_secondary.py", "--ratings", ratings_analysis, "--output", args.output / "secondary"
    ))
    commands.append(run(
        "make_figures.py", "--ratings", ratings_analysis, "--output", args.output / "figures"
    ))
    commands.append(run(
        "summarize_instruction_checks.py", "--ratings", ratings_analysis,
        "--output", args.output / "instruction_checks",
    ))

    inputs = {"ratings_raw": {"path": str(args.ratings_raw), "sha256": sha256(args.ratings_raw)}}
    if args.physiology:
        physiology_prepared = args.processed_dir / "physiology_prepared.csv"
        commands.append(run(
            "prepare_physiology.py", "--physiology", args.physiology,
            "--output", physiology_prepared,
        ))
        commands.append(run(
            "analyze_physiology.py", "--ratings", ratings_analysis,
            "--physiology", physiology_prepared, "--output", args.output / "physiology",
        ))
        inputs["physiology"] = {"path": str(args.physiology), "sha256": sha256(args.physiology)}

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "commands": commands,
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "warning": "Simulated inputs validate code only and must never be reported as study results.",
    }
    (args.output / "pipeline_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"PASS commands={len(commands)} output={args.output.name}")


if __name__ == "__main__":
    main()
