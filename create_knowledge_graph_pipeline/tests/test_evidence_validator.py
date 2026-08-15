from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pipeline.skill_matching.config import load_skill_matching_config
from pipeline.skill_matching.evidence_validator import EvidenceValidator


def _config(tmp_path: Path):
    config = load_skill_matching_config()
    return replace(config, evidence_validation_cache_dir=tmp_path, evidence_validator_max_retries=0)


def _candidate() -> dict:
    return {
        "course_id": "COURSE_1",
        "skill_id": "S1",
        "skill_uri": "https://data.europa.eu/esco/skill/S1",
        "skill_label": "calculate determinants",
        "top_evidence": [{
            "unit_id": "LESSON_1",
            "unit_type": "lesson",
            "query_id": "lesson:1",
            "evidence_text_en": "Determinant calculation and matrix operations",
            "retrieval_score": 0.7,
            "rerank_score": 0.8,
        }],
        "best_retrieval_score": 0.7,
        "best_rerank_score": 0.8,
    }


def test_validator_calls_backend_once_for_one_consolidated_candidate(tmp_path: Path) -> None:
    calls = []

    def backend(candidate):
        calls.append(candidate)
        return {
            "decision": "yes",
            "relation_type": "teaches",
            "confidence": 0.93,
            "evidence_unit_ids": ["LESSON_1"],
            "evidence_quotes": ["Determinant calculation"],
            "reason": "The lesson directly teaches the skill.",
        }

    result = EvidenceValidator(_config(tmp_path), backend).validate([_candidate()])

    assert len(calls) == 1
    assert result[0]["validation"]["decision"] == "yes"


def test_precision_first_config_disables_output_cap_and_uses_strict_confidence() -> None:
    config = load_skill_matching_config()

    assert config.max_skills_per_course is None
    assert config.validation_confidence_threshold == 0.92


def test_hallucinated_quote_fails_closed_as_insufficient(tmp_path: Path) -> None:
    def backend(_candidate):
        return {
            "decision": "yes",
            "relation_type": "teaches",
            "confidence": 0.99,
            "evidence_unit_ids": ["LESSON_1"],
            "evidence_quotes": ["Develop financial derivatives"],
            "reason": "Unsupported claim.",
        }

    result = EvidenceValidator(_config(tmp_path), backend).validate([_candidate()])

    assert result[0]["validation"]["decision"] == "insufficient"


def test_disabled_validator_never_accepts_candidate(tmp_path: Path) -> None:
    config = replace(_config(tmp_path), evidence_validator_enabled=False)
    result = EvidenceValidator(config).validate([_candidate()])
    assert result[0]["validation"]["decision"] == "insufficient"
