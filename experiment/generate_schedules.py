"""Generate counterbalanced A2 schedules from the frozen material manifests."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_PATH = ROOT / "materials" / "emotion_concepts.csv"
STIMULI_PATH = ROOT / "materials" / "stimulus_manifest.csv"
FILLERS_PATH = ROOT / "materials" / "semantic_fillers.csv"
DEFAULT_OUTPUT = ROOT / "materials" / "schedules.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def induced_order(
    stimuli: list[dict[str, str]], valence_by_concept: dict[str, str], rng: random.Random,
    start_valence: str,
) -> list[dict[str, str]]:
    groups = {"positive": [], "negative": []}
    for stimulus in stimuli:
        groups[valence_by_concept[stimulus["concept_id"]]].append(stimulus)
    rng.shuffle(groups["positive"])
    rng.shuffle(groups["negative"])
    other = "negative" if start_valence == "positive" else "positive"
    result = []
    for index in range(max(map(len, groups.values()))):
        for valence in (start_valence, other):
            if index < len(groups[valence]):
                result.append(groups[valence][index])
    return result


def generate(participants: int, seed: int) -> list[dict[str, object]]:
    concepts = read_csv(CONCEPTS_PATH)
    stimuli = read_csv(STIMULI_PATH)
    fillers = read_csv(FILLERS_PATH)
    semantic_items = concepts + fillers
    concept_names = {row["concept_id"]: row["concept_zh"] for row in concepts}
    valence = {row["concept_id"]: row["expected_valence"] for row in concepts}
    rows: list[dict[str, object]] = []

    for number in range(1, participants + 1):
        participant_id = f"P{number:03d}"
        rng = random.Random(seed + number)
        sequence_id = (number - 1) % 8 + 1
        sequence_bits = sequence_id - 1
        semantic_first = (sequence_bits & 1) == 0
        prototype_first = (sequence_bits & 2) != 0
        positive_starts_induced = (sequence_bits & 4) == 0
        semantic_session = "S1" if semantic_first else "S2"
        induced_session = "S2" if semantic_first else "S1"
        condition_order = ["lexical", "prototype"]
        if prototype_first:
            condition_order.reverse()

        for block_order, condition in enumerate(condition_order, start=1):
            ordered_concepts = semantic_items.copy()
            rng.shuffle(ordered_concepts)
            for item_order, concept in enumerate(ordered_concepts, start=1):
                rows.append({
                    "participant_id": participant_id,
                    "sequence_id": sequence_id,
                    "session_id": semantic_session,
                    "session_order": 1 if semantic_first else 2,
                    "session_type": "semantic",
                    "block_order": block_order,
                    "condition": condition,
                    "item_order": item_order,
                    "concept_id": concept["concept_id"],
                    "concept_zh": concept["concept_zh"],
                    "stimulus_id": "",
                    "title": "",
                    "break_after": 0,
                })

        ordered_stimuli = induced_order(
            stimuli, valence, rng, "positive" if positive_starts_induced else "negative"
        )
        for item_order, stimulus in enumerate(ordered_stimuli, start=1):
            rows.append({
                "participant_id": participant_id,
                "sequence_id": sequence_id,
                "session_id": induced_session,
                "session_order": 1 if semantic_first else 2,
                "session_type": "induced",
                "block_order": 1,
                "condition": "induced",
                "item_order": item_order,
                "concept_id": stimulus["concept_id"],
                "concept_zh": concept_names[stimulus["concept_id"]],
                "stimulus_id": stimulus["stimulus_id"],
                "title": stimulus["title"],
                "break_after": 1 if item_order == 6 else 0,
            })
    return rows


def validate(rows: list[dict[str, object]], participants: int) -> None:
    concepts = read_csv(CONCEPTS_PATH)
    stimuli = read_csv(STIMULI_PATH)
    fillers = read_csv(FILLERS_PATH)
    concept_ids = {row["concept_id"] for row in concepts}
    stimulus_ids = {row["stimulus_id"] for row in stimuli}
    semantic_ids = concept_ids | {row["concept_id"] for row in fillers}
    for number in range(1, participants + 1):
        participant_id = f"P{number:03d}"
        person = [row for row in rows if row["participant_id"] == participant_id]
        assert len(person) == (len(concepts) + len(fillers)) * 2 + len(stimuli)
        for condition in ("lexical", "prototype"):
            observed = {
                row["concept_id"] for row in person if row["condition"] == condition
            }
            assert observed == semantic_ids
        induced = sorted(
            (row for row in person if row["condition"] == "induced"),
            key=lambda row: int(row["item_order"]),
        )
        assert {row["stimulus_id"] for row in induced} == stimulus_ids
        assert all(
            induced[index - 1]["concept_id"] != induced[index]["concept_id"]
            for index in range(1, len(induced))
        )
        assert sum(int(row["break_after"]) for row in induced) == 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--participants", type=int, default=48)
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rows = generate(args.participants, args.seed)
    validate(rows, args.participants)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"PASS participants={args.participants} rows={len(rows)} output={args.output.name}")


if __name__ == "__main__":
    main()
