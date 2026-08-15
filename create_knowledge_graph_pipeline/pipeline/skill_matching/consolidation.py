"""Consolidate reranked query-skill pairs before evidence validation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import CandidateEvidence, ConsolidatedCandidate, RerankedCandidate


def _score(candidate: dict[str, Any]) -> tuple[float, float]:
    return float(candidate.get("rerank_score", 0.0)), float(candidate.get("retrieval_score", -1.0))


def _select_diverse_evidence(
    evidence_by_id: dict[str, CandidateEvidence],
    limit: int,
) -> list[CandidateEvidence]:
    ordered = sorted(
        evidence_by_id.values(),
        key=lambda item: (item.rerank_score, item.retrieval_score),
        reverse=True,
    )
    selected: list[CandidateEvidence] = []
    used_types: set[str] = set()
    for evidence in ordered:
        if evidence.unit_type not in used_types:
            selected.append(evidence)
            used_types.add(evidence.unit_type)
            if len(selected) == limit:
                return selected
    for evidence in ordered:
        if evidence not in selected:
            selected.append(evidence)
            if len(selected) == limit:
                break
    return selected


def consolidate_candidates(
    candidates: list[dict[str, Any]],
    *,
    max_evidence: int,
    top_n_per_course: int,
) -> list[dict[str, Any]]:
    """Return at most one validator candidate per ``course_id + skill_uri``."""
    if max_evidence < 1 or top_n_per_course < 1:
        raise ValueError("max_evidence and top_n_per_course must be positive.")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for raw in candidates:
        candidate = RerankedCandidate.model_validate(raw).model_dump(exclude_none=True)
        grouped[(candidate["course_id"], candidate["skill_uri"])].append(candidate)

    consolidated: list[dict[str, Any]] = []
    for (_, _), group in grouped.items():
        best = max(group, key=_score)
        evidence_by_id: dict[str, CandidateEvidence] = {}
        for candidate in group:
            for unit_id, unit_type in zip(candidate["source_unit_ids"], candidate["source_unit_types"]):
                evidence = CandidateEvidence(
                    unit_id=unit_id,
                    unit_type=unit_type,
                    query_id=candidate["query_id"],
                    evidence_text_en=candidate["evidence_text_en"],
                    retrieval_score=candidate["retrieval_score"],
                    rerank_score=candidate["rerank_score"],
                )
                previous = evidence_by_id.get(unit_id)
                if previous is None or (evidence.rerank_score, evidence.retrieval_score) > (
                    previous.rerank_score,
                    previous.retrieval_score,
                ):
                    evidence_by_id[unit_id] = evidence
        selected = _select_diverse_evidence(evidence_by_id, max_evidence)
        consolidated.append(
            ConsolidatedCandidate(
                course_id=best["course_id"],
                skill_id=best["skill_id"],
                skill_uri=best["skill_uri"],
                skill_label=best["skill_label"],
                skill_description=best.get("skill_description"),
                top_evidence=selected,
                best_retrieval_score=max(float(item["retrieval_score"]) for item in group),
                best_rerank_score=max(float(item["rerank_score"]) for item in group),
            ).model_dump(exclude_none=True)
        )

    by_course: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in consolidated:
        by_course[candidate["course_id"]].append(candidate)
    limited: list[dict[str, Any]] = []
    for course_id in sorted(by_course):
        ranked = sorted(
            by_course[course_id],
            key=lambda item: (item["best_rerank_score"], item["best_retrieval_score"]),
            reverse=True,
        )
        limited.extend(ranked[:top_n_per_course])
    return limited

