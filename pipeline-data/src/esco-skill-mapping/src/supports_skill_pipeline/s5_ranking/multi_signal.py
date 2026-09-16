"""Bước 5 — Multi-signal Ranking.

Kết hợp nhiều tín hiệu để ra ranking cuối cùng:
    FinalScore = α · RRFScore + β · EscoXlmrScore + γ · EvidenceScore

Trọng số mặc định: α = β = γ = 1/3 (chưa tối ưu).
"""

from __future__ import annotations

import logging

from ..models.candidate import FusedCandidate, ScoredCandidate
from .evidence_scorer import compute_candidate_evidence

logger = logging.getLogger(__name__)


def _normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalize danh sách scores về [0, 1]."""
    if not scores:
        return []
    min_s = min(scores)
    max_s = max(scores)
    if max_s == min_s:
        return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]


def rank_candidates(
    candidates: list[FusedCandidate],
    support_concepts: list[str],
    course_context: str,
    alpha: float = 1 / 3,
    beta: float = 1 / 3,
    gamma: float = 1 / 3,
    top_k: int = 10,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
) -> list[ScoredCandidate]:
    """Ranking cuối cùng kết hợp 3 tín hiệu.

    Args:
        candidates: Danh sách FusedCandidate từ Bước 4.
        support_concepts: Danh sách support concepts từ Bước 2.
        course_context: Course context từ Bước 1.
        alpha: Weight cho RRF score.
        beta: Weight cho ESCOXLM-R score.
        gamma: Weight cho Evidence score.
        top_k: Số candidates cuối cùng.
        embedding_model: Model cho evidence scoring.

    Returns:
        Top-k ScoredCandidate sorted by final_score descending.
    """
    if not candidates:
        return []

    # Pre-compute evidence: load model + encode sentences 1 lần
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer(embedding_model)
        from .evidence_scorer import _split_into_sentences
        sentences = _split_into_sentences(course_context)
        sent_embeddings = model.encode(
            sentences, convert_to_numpy=True, normalize_embeddings=True,
        ) if sentences else None
    except ImportError:
        model = None
        sentences = None
        sent_embeddings = None
        logger.warning("sentence-transformers not available, evidence scoring disabled.")

    # Collect raw scores for normalization
    rrf_scores = [c.rrf_score for c in candidates]
    escoxlmr_scores = [c.escoxlmr_score for c in candidates]

    # Normalize
    norm_rrf = _normalize_scores(rrf_scores)
    norm_escoxlmr = _normalize_scores(escoxlmr_scores)

    # Compute evidence + final score for each candidate
    scored: list[ScoredCandidate] = []

    for idx, cand in enumerate(candidates):
        # Compute evidence score
        if model is not None and sent_embeddings is not None:
            evidence_text, evidence_score = compute_candidate_evidence(
                concept_origins=cand.concept_origins or support_concepts,
                course_context=course_context,
                _model=model,
                _sent_embeddings=sent_embeddings,
                _sentences=sentences,
            )
        else:
            evidence_text = ""
            evidence_score = 0.0

        # Final score
        final_score = (
            alpha * norm_rrf[idx]
            + beta * norm_escoxlmr[idx]
            + gamma * evidence_score
        )

        scored.append(ScoredCandidate(
            skill_uri=cand.skill_uri,
            skill_label=cand.skill_label,
            skill_description=cand.skill_description,
            skill_type=cand.skill_type,
            rrf_score=cand.rrf_score,
            escoxlmr_score=cand.escoxlmr_score,
            evidence_score=evidence_score,
            final_score=final_score,
            evidence_text=evidence_text,
            concept_origins=cand.concept_origins,
            bm25_rank=cand.bm25_rank,
            faiss_rank=cand.faiss_rank,
            escoxlmr_rank=cand.escoxlmr_rank,
        ))

    # Sort by final_score descending, assign rank
    scored.sort(key=lambda c: c.final_score, reverse=True)
    for rank, cand in enumerate(scored[:top_k], start=1):
        cand.candidate_rank = rank

    result = scored[:top_k]

    logger.info(
        "Multi-signal ranking: %d candidates → top-%d (α=%.3f, β=%.3f, γ=%.3f)",
        len(candidates), len(result), alpha, beta, gamma,
    )

    return result
