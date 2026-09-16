"""Unit test suite cho M5 Supports Pipeline (SUPPORTS_SKILL & SUPPORTS_KNOWLEDGE)."""

import json
import pytest
from pathlib import Path

from pipeline.course_evidence_builder.objective_evidence import build_objective_evidence
from pipeline.esco_concept_provider.concept_metadata_lookup import ConceptMetadataLookup
from pipeline.m5_supports_pipeline import (
    M5Candidate,
    M5PipelineConfig,
    M5SupportRecord,
    M5SupportsPipeline,
)
from pipeline.m5_supports_pipeline.llm_extraction_branch import LLMExtractionBranch
from pipeline.m5_supports_pipeline.rrf_combiner import combine_channels
from pipeline.m5_supports_pipeline.tiering_router import route_m5_tiers
from pipeline.relation_dedup.overlap_resolver import resolve_m4_m5_overlap


@pytest.fixture
def mock_pool_dir(tmp_path):
    skill_pool = [
        {
            "skill_uri": "http://data.europa.eu/esco/skill/s1",
            "preferred_label": "Python programming",
            "description": "Write Python code",
            "skill_type": "skill/competence",
        },
        {
            "skill_uri": "http://data.europa.eu/esco/skill/s2",
            "preferred_label": "Database management",
            "description": "Manage SQL databases",
            "skill_type": "skill/competence",
        },
    ]
    knowledge_pool = [
        {
            "skill_uri": "http://data.europa.eu/esco/skill/k1",
            "preferred_label": "Computer science principles",
            "description": "Fundamental CS knowledge",
            "skill_type": "knowledge",
        },
    ]
    (tmp_path / "skill_pool.json").write_text(json.dumps(skill_pool), encoding="utf-8")
    (tmp_path / "knowledge_pool.json").write_text(json.dumps(knowledge_pool), encoding="utf-8")
    return tmp_path


def test_build_objective_evidence():
    evidence = build_objective_evidence(
        course_code="SC6014",
        muc_tieu_texts=["Hiểu kiến thức lập trình cơ bản."],
        mo_ta_tom_tat_en="Basic programming course description.",
    )
    assert len(evidence) == 1
    assert evidence[0].course_code == "SC6014"
    assert "Hiểu kiến thức" in evidence[0].text
    assert "Basic programming" in evidence[0].text


def test_rrf_combiner():
    retrieval = [
        M5Candidate("http://esco/s1", "S1", "desc", "skill", score_retrieval=0.9),
        M5Candidate("http://esco/s2", "S2", "desc", "skill", score_retrieval=0.8),
    ]
    llm = [
        M5Candidate("http://esco/s2", "S2", "desc", "skill", score_llm=0.95),
        M5Candidate("http://esco/s3", "S3", "desc", "skill", score_llm=0.7),
    ]

    merged = combine_channels(retrieval, llm, concept_type="skill", rrf_k=60)
    assert len(merged) == 3
    # s2 appears in both -> highest RRF score
    assert merged[0].skill_uri == "http://esco/s2"
    assert merged[0].score_final > merged[1].score_final


def test_tiering_router_hard_caps():
    candidates = [
        M5Candidate(f"http://esco/s{i}", f"Skill {i}", "desc", "skill", score_final=0.03 - 0.001 * i)
        for i in range(20)
    ]
    config = M5PipelineConfig(course_type="FOUNDATIONAL")
    accepted, rejected = route_m5_tiers(candidates, config, concept_type="skill")

    # Hard cap for FOUNDATIONAL skill is 7
    assert len(accepted) == 7
    assert len(rejected) == 13
    assert rejected[0].reject_reason == "exceeds_hard_cap_7"


def test_overlap_resolver():
    m4_records = ["http://esco/s1", "http://esco/s2"]
    m5_candidates = [
        M5Candidate("http://esco/s1", "S1", "desc", "skill"),
        M5Candidate("http://esco/s3", "S3", "desc", "skill"),
    ]

    deduped, removed = resolve_m4_m5_overlap(m4_records, m5_candidates, concept_type="skill")
    assert len(deduped) == 1
    assert deduped[0].skill_uri == "http://esco/s3"
    assert len(removed) == 1
    assert removed[0].skill_uri == "http://esco/s1"


def test_m5_supports_pipeline_end_to_end(mock_pool_dir, tmp_path):
    config = M5PipelineConfig(
        pool_dir=mock_pool_dir,
        output_dir=tmp_path / "supports",
        course_type="SPECIALIZED",
        llm_enabled=False,
    )
    lookup = ConceptMetadataLookup(mock_pool_dir)
    pipeline = M5SupportsPipeline(config=config, metadata_lookup=lookup)

    records, accepted, rejected = pipeline.run_course(
        course_code="TEST101",
        course_title="Test Course",
        muc_tieu=["Understand database concepts."],
        mo_ta_tom_tat_en="Course covering databases and Python.",
    )

    out_dir = tmp_path / "supports" / "TEST101"
    assert out_dir.exists() or (tmp_path / "supports" / "_candidate_logs").exists()
