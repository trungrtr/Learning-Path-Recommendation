"""Tests for mandatory pre-validation consolidation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.skill_matching.consolidation import consolidate_candidates


def _candidate(query_id: str, unit_id: str, unit_type: str, rerank: float) -> dict:
    return {
        "course_id": "C1",
        "query_id": query_id,
        "query_type": unit_type,
        "retrieval_text_en": f"Course > {query_id}",
        "evidence_text_en": query_id,
        "source_unit_ids": [unit_id],
        "source_unit_types": [unit_type],
        "skill_id": "S1",
        "skill_uri": "esco:S1",
        "skill_label": "Skill one",
        "retrieval_rank": 1,
        "retrieval_score": 0.7,
        "rerank_score": rerank,
    }


def test_same_course_skill_becomes_one_candidate_with_diverse_evidence() -> None:
    candidates = [
        _candidate("CLO evidence", "CLO1", "clo", 0.8),
        _candidate("Lesson evidence", "L1", "lesson", 0.9),
        _candidate("Duplicate lesson", "L1", "lesson", 0.7),
    ]

    consolidated = consolidate_candidates(candidates, max_evidence=2, top_n_per_course=10)

    assert len(consolidated) == 1
    assert {item["unit_id"] for item in consolidated[0]["top_evidence"]} == {"CLO1", "L1"}
    assert consolidated[0]["best_rerank_score"] == 0.9


def test_top_n_limits_skills_per_course_after_grouping() -> None:
    candidates = []
    for index, score in enumerate((0.9, 0.8, 0.7), start=1):
        candidate = _candidate(f"Evidence {index}", f"L{index}", "lesson", score)
        candidate["skill_id"] = f"S{index}"
        candidate["skill_uri"] = f"esco:S{index}"
        candidates.append(candidate)

    consolidated = consolidate_candidates(candidates, max_evidence=1, top_n_per_course=2)

    assert [item["skill_uri"] for item in consolidated] == ["esco:S1", "esco:S2"]

