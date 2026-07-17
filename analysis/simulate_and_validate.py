"""Generate deterministic mock data and validate the A2 data contract."""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONCEPTS_PATH = ROOT / "materials" / "emotion_concepts.csv"
STIMULI_PATH = ROOT / "materials" / "stimulus_manifest.csv"
FILLERS_PATH = ROOT / "materials" / "semantic_fillers.csv"
OUT_DIR = ROOT / "data" / "simulated"
RATINGS_PATH = OUT_DIR / "ratings_long.csv"
PHYSIOLOGY_PATH = OUT_DIR / "physiology_trials.csv"
SEED = 20260714


def clamp_rating(value: float) -> int:
    return max(1, min(9, round(value)))


def read_concepts() -> list[dict[str, str]]:
    with CONCEPTS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        concepts = list(csv.DictReader(handle))
    if not concepts:
        raise ValueError("No concepts found")
    return concepts


def read_stimuli() -> list[dict[str, str]]:
    with STIMULI_PATH.open(encoding="utf-8-sig", newline="") as handle:
        stimuli = list(csv.DictReader(handle))
    if not stimuli:
        raise ValueError("No stimuli found")
    return stimuli


def read_fillers() -> list[dict[str, str]]:
    with FILLERS_PATH.open(encoding="utf-8-sig", newline="") as handle:
        fillers = list(csv.DictReader(handle))
    if not fillers:
        raise ValueError("No semantic fillers found")
    return fillers


def expected_centroid(concept: dict[str, str]) -> tuple[float, float, float]:
    valence = 7.3 if concept["expected_valence"] == "positive" else 2.7
    arousal_map = {"medium": 5.5, "medium_high": 6.3, "high": 7.0}
    arousal = arousal_map[concept["expected_arousal"]]
    dominance_map = {"low": 3.0, "medium": 5.5, "medium_high": 6.2, "contextual": 5.0}
    dominance = dominance_map.get(concept["expected_dominance"], 5.5)
    return valence, arousal, dominance


def generate() -> None:
    random.seed(SEED)
    concepts = read_concepts()
    stimuli = read_stimuli()
    fillers = read_fillers()
    stimuli_by_concept = {
        concept["concept_id"]: [
            stimulus for stimulus in stimuli
            if stimulus["concept_id"] == concept["concept_id"]
        ]
        for concept in concepts
    }
    if any(len(items) != 2 for items in stimuli_by_concept.values()):
        raise ValueError("Simulation expects exactly two candidate stimuli per concept")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    rating_fields = [
        "participant_id", "concept_id", "condition", "stimulus_id",
        "session_id", "session_order", "block_order", "item_order",
        "valence", "arousal", "dominance", "target_emotion_intensity",
        "intensity_joy", "intensity_amusement", "intensity_tenderness",
        "intensity_anger", "intensity_sadness", "intensity_fear",
        "intensity_disgust", "discomfort", "familiarity", "self_relevance",
        "response_time_ms",
        "attention_check", "attention_check_rate", "instruction_check_correct",
        "instruction_check_response", "notes",
    ]
    physiology_fields = [
        "participant_id", "concept_id", "stimulus_id", "baseline_start_s",
        "baseline_end_s", "stimulus_start_s", "stimulus_end_s",
        "recovery_end_s", "eda_baseline", "eda_stimulus", "eda_delta",
        "hr_baseline", "hr_stimulus", "hr_delta", "ibi_baseline",
        "ibi_stimulus", "signal_qc_eda", "signal_qc_ecg_ppg",
        "exclusion_reason",
    ]

    ratings: list[dict[str, object]] = []
    physiology: list[dict[str, object]] = []

    for participant_index in range(1, 37):
        participant_id = f"P{participant_index:03d}"
        session_order = 1 if participant_index % 2 else 2
        semantic_conditions = ["lexical", "prototype"]
        random.shuffle(semantic_conditions)
        semantic_block_order = {
            condition: index for index, condition in enumerate(semantic_conditions, start=1)
        }
        semantic_session = "S1" if session_order == 1 else "S2"
        induced_session = "S2" if session_order == 1 else "S1"
        person_shift = random.gauss(0, 0.45)

        for item_order, concept in enumerate(concepts, start=1):
            concept_id = concept["concept_id"]
            base_v, base_a, base_d = expected_centroid(concept)
            lexical = (
                base_v + random.gauss(0, 0.8),
                base_a + random.gauss(0, 0.9),
                base_d + random.gauss(0, 1.0),
            )
            prototype = (
                base_v + person_shift + random.gauss(0, 0.55),
                base_a + person_shift / 2 + random.gauss(0, 0.65),
                base_d + random.gauss(0, 0.75),
            )
            for condition, scores in (("lexical", lexical), ("prototype", prototype)):
                ratings.append({
                    "participant_id": participant_id,
                    "concept_id": concept_id,
                    "condition": condition,
                    "stimulus_id": "",
                    "session_id": semantic_session,
                    "session_order": session_order,
                    "block_order": semantic_block_order.get(condition, 1),
                    "item_order": item_order,
                    "valence": clamp_rating(scores[0]),
                    "arousal": clamp_rating(scores[1]),
                    "dominance": clamp_rating(scores[2]),
                    "target_emotion_intensity": "",
                    "intensity_joy": "",
                    "intensity_amusement": "",
                    "intensity_tenderness": "",
                    "intensity_anger": "",
                    "intensity_sadness": "",
                    "intensity_fear": "",
                    "intensity_disgust": "",
                    "discomfort": "",
                    "familiarity": random.randint(1, 9),
                    "self_relevance": random.randint(1, 9),
                    "response_time_ms": random.randint(1200, 6500),
                    "attention_check": 1,
                    "attention_check_rate": 1.0,
                    "instruction_check_correct": 1,
                    "instruction_check_response": condition,
                    "notes": "SIMULATED",
                })

            for stimulus_index, stimulus in enumerate(stimuli_by_concept[concept_id], start=1):
                induced = (
                    base_v + person_shift + random.gauss(0, 0.75),
                    base_a + random.gauss(0, 0.75),
                    base_d + random.gauss(0, 0.9),
                )
                ratings.append({
                    "participant_id": participant_id,
                    "concept_id": concept_id,
                    "condition": "induced",
                    "stimulus_id": stimulus["stimulus_id"],
                    "session_id": induced_session,
                    "session_order": session_order,
                    "block_order": 1,
                    "item_order": (item_order - 1) * 2 + stimulus_index,
                    "valence": clamp_rating(induced[0]),
                    "arousal": clamp_rating(induced[1]),
                    "dominance": clamp_rating(induced[2]),
                    "target_emotion_intensity": clamp_rating(base_a),
                    "intensity_joy": clamp_rating(base_a) if concept_id == "JOY" else random.randint(1, 4),
                    "intensity_amusement": clamp_rating(base_a) if concept_id == "AMUSEMENT" else random.randint(1, 4),
                    "intensity_tenderness": clamp_rating(base_a) if concept_id == "TENDERNESS" else random.randint(1, 4),
                    "intensity_anger": clamp_rating(base_a) if concept_id == "ANGER" else random.randint(1, 4),
                    "intensity_sadness": clamp_rating(base_a) if concept_id == "SADNESS" else random.randint(1, 4),
                    "intensity_fear": clamp_rating(base_a) if concept_id == "FEAR" else random.randint(1, 4),
                    "intensity_disgust": random.randint(2, 6) if concept_id == "ANGER" else random.randint(1, 4),
                    "discomfort": random.randint(5, 8) if concept["expected_valence"] == "negative" else random.randint(1, 4),
                    "familiarity": random.randint(1, 9),
                    "self_relevance": random.randint(1, 9),
                    "response_time_ms": random.randint(1200, 6500),
                    "attention_check": 1,
                    "attention_check_rate": 1.0,
                    "instruction_check_correct": 1,
                    "instruction_check_response": "induced",
                    "notes": "SIMULATED",
                })

                eda_baseline = max(0.2, random.gauss(3.0, 0.7))
                eda_delta = max(-0.2, (induced[1] - 3) * 0.10 + random.gauss(0, 0.12))
                hr_baseline = random.gauss(70, 7)
                hr_delta = (induced[1] - 5) * 0.8 + random.gauss(0, 1.8)
                physiology.append({
                    "participant_id": participant_id,
                    "concept_id": concept_id,
                    "stimulus_id": stimulus["stimulus_id"],
                    "baseline_start_s": 0,
                    "baseline_end_s": 30,
                    "stimulus_start_s": 30,
                    "stimulus_end_s": 30 + int(stimulus["duration_s"]),
                    "recovery_end_s": 90 + int(stimulus["duration_s"]),
                    "eda_baseline": round(eda_baseline, 4),
                    "eda_stimulus": round(eda_baseline + eda_delta, 4),
                    "eda_delta": round(eda_delta, 4),
                    "hr_baseline": round(hr_baseline, 3),
                    "hr_stimulus": round(hr_baseline + hr_delta, 3),
                    "hr_delta": round(hr_delta, 3),
                    "ibi_baseline": round(60_000 / hr_baseline, 3),
                    "ibi_stimulus": round(60_000 / (hr_baseline + hr_delta), 3),
                    "signal_qc_eda": "pass",
                    "signal_qc_ecg_ppg": "pass",
                    "exclusion_reason": "",
                })

        for filler_index, filler in enumerate(fillers, start=len(concepts) + 1):
            for condition in ("lexical", "prototype"):
                ratings.append({
                    "participant_id": participant_id,
                    "concept_id": filler["concept_id"],
                    "condition": condition,
                    "stimulus_id": "",
                    "session_id": semantic_session,
                    "session_order": session_order,
                    "block_order": semantic_block_order[condition],
                    "item_order": filler_index,
                    "valence": random.randint(1, 9),
                    "arousal": random.randint(1, 9),
                    "dominance": random.randint(1, 9),
                    "target_emotion_intensity": "",
                    "intensity_joy": "",
                    "intensity_amusement": "",
                    "intensity_tenderness": "",
                    "intensity_anger": "",
                    "intensity_sadness": "",
                    "intensity_fear": "",
                    "intensity_disgust": "",
                    "discomfort": "",
                    "familiarity": random.randint(1, 9),
                    "self_relevance": random.randint(1, 9),
                    "response_time_ms": random.randint(1200, 6500),
                    "attention_check": 1,
                    "attention_check_rate": 1.0,
                    "instruction_check_correct": 1,
                    "instruction_check_response": condition,
                    "notes": "SIMULATED_FILLER",
                })

    with RATINGS_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rating_fields)
        writer.writeheader()
        writer.writerows(ratings)

    with PHYSIOLOGY_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=physiology_fields)
        writer.writeheader()
        writer.writerows(physiology)


def validate() -> None:
    with RATINGS_PATH.open(encoding="utf-8", newline="") as handle:
        ratings = list(csv.DictReader(handle))
    with PHYSIOLOGY_PATH.open(encoding="utf-8", newline="") as handle:
        physiology = list(csv.DictReader(handle))

    concept_count = len(read_concepts())
    stimulus_count = len(read_stimuli())
    filler_count = len(read_fillers())
    expected_rating_rows = 36 * ((concept_count + filler_count) * 2 + stimulus_count)
    expected_physio_rows = 36 * stimulus_count
    assert len(ratings) == expected_rating_rows, (len(ratings), expected_rating_rows)
    assert len(physiology) == expected_physio_rows, (len(physiology), expected_physio_rows)

    rating_keys = set()
    for row in ratings:
        key = (row["participant_id"], row["concept_id"], row["condition"], row["stimulus_id"])
        assert key not in rating_keys, f"Duplicate rating key: {key}"
        rating_keys.add(key)
        assert row["condition"] in {"lexical", "prototype", "induced"}
        for dimension in ("valence", "arousal", "dominance"):
            assert 1 <= int(row[dimension]) <= 9
        assert bool(row["stimulus_id"]) == (row["condition"] == "induced")
        intensity_fields = [
            "intensity_joy", "intensity_amusement", "intensity_tenderness",
            "intensity_anger", "intensity_sadness", "intensity_fear", "intensity_disgust",
        ]
        if row["condition"] == "induced":
            assert all(1 <= int(row[field]) <= 9 for field in intensity_fields)
            assert 1 <= int(row["discomfort"]) <= 9
        else:
            assert all(row[field] == "" for field in intensity_fields)

    physio_keys = {
        (row["participant_id"], row["concept_id"], row["stimulus_id"])
        for row in physiology
    }
    induced_keys = {
        (row["participant_id"], row["concept_id"], row["stimulus_id"])
        for row in ratings if row["condition"] == "induced"
    }
    assert physio_keys == induced_keys, "Physiology and induced-rating keys do not align"
    assert all(math.isfinite(float(row["eda_delta"])) for row in physiology)

    print(f"PASS ratings={len(ratings)} physiology={len(physiology)} seed={SEED}")


if __name__ == "__main__":
    generate()
    validate()
