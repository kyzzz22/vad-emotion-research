"""Build the static browser-task configuration from validated CSV materials."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "materials"
OUTPUT = ROOT / "experiment" / "web" / "config.json"


def read_csv(name: str) -> list[dict[str, str]]:
    with (MATERIALS / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    config = {
        "version": "0.2.0-data-pre",
        "schedule": read_csv("schedules.csv"),
        "rating_items": read_csv("rating_items.csv"),
        "event_codes": read_csv("event_codes.csv"),
        "timing_ms": {
            "baseline": 30000,
            "recovery": 60000,
            "mid_break": 180000,
            "semantic_block_break": 180000,
        },
        "media_path_template": "media/{stimulus_id}.mp4",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"PASS schedule={len(config['schedule'])} ratings={len(config['rating_items'])} "
        f"events={len(config['event_codes'])} output={OUTPUT.name}"
    )


if __name__ == "__main__":
    main()
