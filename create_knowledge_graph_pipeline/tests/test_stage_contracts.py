"""P0 contract tests for every external boundary introduced by the refactor."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_course.mo_hinh import ExtractedDocument
from pipeline.extract_translate.models import TranslatedUnit
from pipeline.kg_export.models import CourseSkillRelationship, KGExport
from pipeline.merge.models import CanonicalDocument
from pipeline.skill_matching.models import (
    CourseSkillResult,
    EvidenceValidationResult,
    SkillCandidate,
)


def _json_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_existing_layer_contract_versions_remain_locked() -> None:
    assert ExtractedDocument.model_fields["schema_version"].default == "1.2"
    assert CanonicalDocument.model_fields["schema_version"].default == "2.3"


def test_translated_unit_reuses_canonical_lesson_id_and_preserves_hierarchy() -> None:
    unit = TranslatedUnit(
        course_id="COURSE_BS6002",
        unit_id="COURSE_BS6002_L1",
        unit_type="lesson",
        internal_course_code="BS6002",
        course_name_vi="Giải tích",
        course_name_en="Calculus",
        lesson_id="COURSE_BS6002_L1",
        chapter_id="COURSE_BS6002_CH1",
        chapter_title_vi="Tích phân kép",
        chapter_title_en="Double Integrals",
        text_vi="Tính toán công và lực",
        text_src="Tính toán công và lực",
        text_en="Calculation of Work and Force",
    )

    assert unit.unit_id == unit.lesson_id
    assert unit.chapter_id == "COURSE_BS6002_CH1"
    assert set(_json_schema("translated_unit_schema.json")["properties"]) == set(
        TranslatedUnit.model_fields
    )


def test_translated_unit_rejects_generated_or_mismatched_unit_id() -> None:
    with pytest.raises(ValidationError):
        TranslatedUnit(
            course_id="COURSE_1",
            unit_id="lesson_1",
            unit_type="lesson",
            lesson_id="COURSE_1_L1",
            text_vi="Bài học",
            text_src="Bài học",
            text_en="Lesson",
        )


def test_skill_candidate_contract_keeps_retrieval_and_evidence_text_separate() -> None:
    candidate = SkillCandidate(
        course_id="COURSE_BS6002",
        query_id="lesson:COURSE_BS6002_L1",
        query_type="lesson",
        retrieval_text_en="Calculus > Double Integrals > Calculation of Work and Force",
        evidence_text_en="Calculation of Work and Force",
        source_unit_ids=["COURSE_BS6002_L1"],
        source_unit_types=["lesson"],
        skill_id="S1",
        skill_uri="https://data.europa.eu/esco/skill/S1",
        skill_label="perform mathematical calculations",
        retrieval_rank=1,
        retrieval_score=0.72,
    )

    assert candidate.retrieval_text_en != candidate.evidence_text_en
    assert set(_json_schema("skill_candidate_schema.json")["properties"]) == set(
        SkillCandidate.model_fields
    )


def test_skill_candidate_rejects_broken_provenance_alignment() -> None:
    with pytest.raises(ValidationError):
        SkillCandidate(
            course_id="COURSE_1",
            query_id="Q1",
            query_type="lesson",
            retrieval_text_en="Course > Chapter > Lesson",
            evidence_text_en="Lesson",
            source_unit_ids=["L1", "L2"],
            source_unit_types=["lesson"],
            skill_id="S1",
            skill_uri="https://data.europa.eu/esco/skill/S1",
            skill_label="Skill",
            retrieval_rank=1,
            retrieval_score=0.5,
        )


def test_evidence_validator_contract_cannot_accept_without_evidence() -> None:
    with pytest.raises(ValidationError):
        EvidenceValidationResult(
            course_id="COURSE_1",
            skill_uri="https://data.europa.eu/esco/skill/S1",
            decision="yes",
            relation_type="teaches",
            confidence=0.9,
            reason="No evidence was supplied.",
        )


def test_empty_course_skill_result_is_valid_and_schema_locked() -> None:
    result = CourseSkillResult(course_id="COURSE_EMPTY")

    assert result.model_dump() == {
        "schema_version": "1.0",
        "stage": "course_skill_output",
        "calibration_status": "experimental",
        "limitations": [],
        "course_id": "COURSE_EMPTY",
        "course_code": None,
        "internal_course_code": None,
        "matched_skills": [],
    }
    assert set(_json_schema("course_skill_output_schema.json")["properties"]) == set(
        CourseSkillResult.model_fields
    )


def test_kg_export_contract_and_schema_keep_description_as_node() -> None:
    export = KGExport()
    schema = _json_schema("kg_schema.json")

    assert export.schema_version == "1.0"
    assert "descriptions" in KGExport.model_fields
    assert set(schema["properties"]) == set(KGExport.model_fields)
    assert "HAS_DESCRIPTION" in schema["$defs"]["entityRelationship"]["properties"][
        "relationship_type"
    ]["enum"]


def test_kg_course_skill_evidence_must_be_aligned() -> None:
    with pytest.raises(ValidationError):
        CourseSkillRelationship(
            course_id="COURSE_1",
            skill_uri="https://data.europa.eu/esco/skill/S1",
            relationship_type="TEACHES_SKILL",
            retrieval_score=0.7,
            rerank_score=0.8,
            validation_confidence=0.9,
            evidence_unit_ids=["CLO_1", "LESSON_1"],
            evidence_quotes=["One quote"],
        )
