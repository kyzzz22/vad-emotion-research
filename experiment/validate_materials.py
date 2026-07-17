"""Validate cross-file contracts for the A2 experiment package."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATERIALS = ROOT / "materials"


def read_dicts(name: str) -> list[dict[str, str]]:
    path = MATERIALS / name
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or None in reader.fieldnames:
            raise ValueError(f"Invalid header in {name}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"Ragged rows in {name}")
    return rows


def unique(rows: list[dict[str, str]], field: str, name: str) -> set[str]:
    values = [row[field] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {field} in {name}")
    return set(values)


def main() -> None:
    concepts = read_dicts("emotion_concepts.csv")
    stimuli = read_dicts("stimulus_manifest.csv")
    fillers = read_dicts("semantic_fillers.csv")
    ratings = read_dicts("rating_items.csv")
    events = read_dicts("event_codes.csv")
    schedules = read_dicts("schedules.csv")

    concept_ids = unique(concepts, "concept_id", "emotion_concepts.csv")
    stimulus_ids = unique(stimuli, "stimulus_id", "stimulus_manifest.csv")
    filler_ids = unique(fillers, "concept_id", "semantic_fillers.csv")
    unique(ratings, "item_id", "rating_items.csv")
    unique(events, "event_code", "event_codes.csv")
    if len(concept_ids) != 6 or len(stimulus_ids) != 12:
        raise ValueError("Frozen candidate design requires 6 concepts and 12 stimuli")
    if concept_ids & filler_ids or len(filler_ids) != 12:
        raise ValueError("Semantic fillers must contain 12 non-target unique IDs")
    if {row["concept_id"] for row in stimuli} != concept_ids:
        raise ValueError("Every concept must have candidate stimuli")
    for concept_id in concept_ids:
        count = sum(row["concept_id"] == concept_id for row in stimuli)
        if count != 2:
            raise ValueError(f"{concept_id} has {count} stimuli; expected 2")

    for condition in ("lexical", "prototype", "induced"):
        constructs = {
            row["construct"] for row in ratings
            if row["scope"] == condition and row["analysis_role"] == "primary_dimension"
        }
        if constructs != {"valence", "arousal", "dominance"}:
            raise ValueError(f"Incomplete VAD items for {condition}: {constructs}")
    required_events = {row["event_name"] for row in events if row["required"] == "yes"}
    if not {"SESSION_START", "TRIAL_READY", "RATING_START", "RATING_END", "SESSION_END"}.issubset(required_events):
        raise ValueError("Required event markers are incomplete")

    participant_ids = sorted({row["participant_id"] for row in schedules})
    if len(participant_ids) != 48:
        raise ValueError("Expected 48 preallocated participant schedules")
    sequence_counts: dict[tuple[str, str, str], int] = {}
    for participant_id in participant_ids:
        person = [row for row in schedules if row["participant_id"] == participant_id]
        if len(person) != 48:
            raise ValueError(f"{participant_id} has {len(person)} rows; expected 48")
        semantic_ids = concept_ids | filler_ids
        for condition in ("lexical", "prototype"):
            observed = {
                row["concept_id"] for row in person if row["condition"] == condition
            }
            if observed != semantic_ids:
                raise ValueError(f"Incomplete {condition} schedule for {participant_id}")
        induced_ids = {
            row["stimulus_id"] for row in person if row["condition"] == "induced"
        }
        if induced_ids != stimulus_ids:
            raise ValueError(f"Incomplete induced schedule for {participant_id}")
        semantic = [row for row in person if row["session_type"] == "semantic"]
        induced = sorted(
            (row for row in person if row["session_type"] == "induced"),
            key=lambda row: int(row["item_order"]),
        )
        semantic_first = "yes" if semantic[0]["session_id"] == "S1" else "no"
        first_semantic_condition = min(semantic, key=lambda row: (int(row["block_order"]), int(row["item_order"])))["condition"]
        concept_valence = {row["concept_id"]: row["expected_valence"] for row in concepts}
        first_induced_valence = concept_valence[induced[0]["concept_id"]]
        key = (semantic_first, first_semantic_condition, first_induced_valence)
        sequence_counts[key] = sequence_counts.get(key, 0) + 1

    if len(sequence_counts) != 8 or set(sequence_counts.values()) != {6}:
        raise ValueError(f"The three counterbalancing factors are not orthogonal: {sequence_counts}")

    tracker_path = ROOT / "operations" / "participant_tracker.csv"
    with tracker_path.open(encoding="utf-8-sig", newline="") as handle:
        tracker = list(csv.DictReader(handle))
    tracker_ids = unique(tracker, "participant_id", "participant_tracker.csv")
    if tracker_ids != set(participant_ids):
        raise ValueError("Participant tracker IDs do not match schedules")
    tracker_by_id = {row["participant_id"]: row for row in tracker}
    for participant_id in participant_ids:
        person = [row for row in schedules if row["participant_id"] == participant_id]
        row = tracker_by_id[participant_id]
        s1_type = next(item["session_type"] for item in person if item["session_id"] == "S1")
        s2_type = next(item["session_type"] for item in person if item["session_id"] == "S2")
        if row["session_1_type"] != s1_type or row["session_2_type"] != s2_type:
            raise ValueError(f"Tracker session types do not match schedule for {participant_id}")
        if row["sequence_id"] != person[0]["sequence_id"]:
            raise ValueError(f"Tracker sequence does not match schedule for {participant_id}")

    print(
        f"PASS concepts={len(concepts)} stimuli={len(stimuli)} "
        f"fillers={len(fillers)} ratings={len(ratings)} events={len(events)} "
        f"schedules={len(schedules)} tracker={len(tracker)}"
    )


if __name__ == "__main__":
    main()
