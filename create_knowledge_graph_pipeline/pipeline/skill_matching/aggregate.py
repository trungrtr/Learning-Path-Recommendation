"""Aggregate only evidence-validated ESCO candidates into course outputs."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import CourseSkillEvidence, CourseSkillResult, MatchedSkill, ValidatedCandidate


def aggregate_by_course(
    validated_candidates: list[dict[str, Any]],
    *,
    course_metadata: dict[str, dict[str, str | None]] | None = None,
    calibration_status: str = "experimental",
    limitations: list[str] | None = None,
    max_skills_per_course: int | None = None,
) -> list[dict[str, Any]]:
    """Return one strict result per course, accepting only validator decision ``yes``.

    If *max_skills_per_course* is set, keep only the top-N skills ranked by
    (validation_confidence DESC, rerank_score DESC, retrieval_score DESC).
    """
    metadata = course_metadata or {}
    grouped: dict[str, list[MatchedSkill]] = defaultdict(list)

    for raw in validated_candidates:
        item = ValidatedCandidate.model_validate(raw)
        validation = item.validation
        if validation.decision != "yes":
            continue
        evidence_by_id = {evidence.unit_id: evidence for evidence in item.candidate.top_evidence}
        evidence = [
            CourseSkillEvidence(
                unit_id=unit_id,
                unit_type=evidence_by_id[unit_id].unit_type,
                quote=quote,
            )
            for unit_id, quote in zip(validation.evidence_unit_ids, validation.evidence_quotes)
        ]
        grouped[item.candidate.course_id].append(
            MatchedSkill(
                skill_id=item.candidate.skill_id,
                skill_uri=item.candidate.skill_uri,
                skill_label=item.candidate.skill_label,
                skill_description=item.candidate.skill_description,
                relation_type=validation.relation_type,
                retrieval_score=item.candidate.best_retrieval_score,
                rerank_score=item.candidate.best_rerank_score,
                validation_confidence=validation.confidence,
                evidence=evidence,
            )
        )

    course_ids = set(metadata) | {item["candidate"]["course_id"] for item in validated_candidates}
    results: list[dict[str, Any]] = []
    for course_id in sorted(course_ids):
        course = metadata.get(course_id, {})
        skills = sorted(
            grouped.get(course_id, []),
            key=lambda skill: (skill.validation_confidence, skill.rerank_score, skill.retrieval_score),
            reverse=True,
        )
        if max_skills_per_course is not None and len(skills) > max_skills_per_course:
            skills = skills[:max_skills_per_course]
        result = CourseSkillResult(
            calibration_status=calibration_status,
            limitations=limitations or [],
            course_id=course_id,
            course_code=course.get("course_code"),
            internal_course_code=course.get("internal_course_code"),
            matched_skills=skills,
        )
        results.append(result.model_dump(mode="json", exclude_none=True))
    return results
