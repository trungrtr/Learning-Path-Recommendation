"""Tests for deterministic hierarchy-aware V1 query generation."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.skill_matching.query_builder import build_match_queries


def _config(max_tokens: int = 180, overlap: int = 20) -> SimpleNamespace:
    return SimpleNamespace(
        description_chunk_tokens=max_tokens,
        description_chunk_overlap_tokens=overlap,
    )


def _pool() -> SimpleNamespace:
    return SimpleNamespace(model=SimpleNamespace(tokenizer=None))


def test_query_builder_uses_course_chapter_lesson_hierarchy() -> None:
    units = [
        {"course_id": "C1", "unit_id": "C1", "unit_type": "name", "text_en": "Calculus"},
        {
            "course_id": "C1",
            "unit_id": "C1_CH1",
            "unit_type": "chapter",
            "chapter_id": "C1_CH1",
            "text_en": "Double Integrals",
        },
        {
            "course_id": "C1",
            "unit_id": "C1_L1",
            "unit_type": "lesson",
            "chapter_id": "C1_CH1",
            "chapter_title_en": "Double Integrals",
            "text_en": "Calculation of Work and Force",
        },
    ]

    queries = build_match_queries(units, "BS6002", _pool(), _config())

    lesson = next(query for query in queries if query["query_type"] == "lesson")
    assert lesson["retrieval_text_en"] == "Calculus > Double Integrals > Calculation of Work and Force"
    assert lesson["evidence_text_en"] == "Calculation of Work and Force"
    assert lesson["source_unit_ids"] == ["C1_L1"]
    assert not any(query["query_type"] == "topic_ability" for query in queries)


def test_description_is_chunked_deterministically_with_provenance() -> None:
    units = [
        {"course_id": "C1", "unit_id": "C1", "unit_type": "name", "text_en": "Course"},
        {
            "course_id": "C1",
            "unit_id": "C1_DESC",
            "unit_type": "description",
            "description_id": "C1_DESC",
            "text_en": "one two three four five six seven eight nine ten",
        },
    ]

    queries = build_match_queries(units, "C1", _pool(), _config(max_tokens=4, overlap=1))
    course_queries = [query for query in queries if query["query_type"] == "course"]

    assert len(course_queries) >= 3
    assert [query["chunk_index"] for query in course_queries] == list(range(len(course_queries)))
    assert all(query["source_unit_ids"] == ["C1_DESC"] for query in course_queries)
    assert all(len(query["evidence_text_en"].split()) <= 4 for query in course_queries)


def test_query_builder_uses_course_name_when_description_is_missing() -> None:
    units = [{"course_id": "C1", "unit_id": "C1", "unit_type": "name", "text_en": "Database Systems"}]

    queries = build_match_queries(units, "IT6006", _pool(), _config())

    assert queries == [
        {
            "course_id": "C1",
            "query_id": "course:C1",
            "query_type": "course",
            "retrieval_text_en": "Database Systems",
            "evidence_text_en": "Database Systems",
            "source_unit_ids": ["C1"],
            "source_unit_types": ["name"],
        }
    ]

