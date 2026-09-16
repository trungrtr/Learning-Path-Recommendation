"""Bước 3.3 — ESCOXLM-R Domain-Specific Retrieval.

Tính điểm tương đồng semantic domain-specific giữa support concepts
và ESCO skill descriptions bằng ESCOXLM-R (pretrained trên ESCO taxonomy).

Công nghệ: ESCOXLM-R checkpoint + Hugging Face Transformers + PyTorch.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from ..models.candidate import SupportCandidate

logger = logging.getLogger(__name__)


def _load_metadata(metadata_path: str | Path) -> list[dict[str, Any]]:
    """Load ESCO metadata."""
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_MODEL_CACHE: Any = None
_CANDIDATE_EMBEDDINGS_CACHE: Any = None
_CANDIDATE_TEXTS_CACHE: list[str] | None = None

def _compute_escoxlmr_scores(
    query_texts: list[str],
    candidate_texts: list[str],
    model_name: str,
) -> np.ndarray:
    global _MODEL_CACHE, _CANDIDATE_EMBEDDINGS_CACHE, _CANDIDATE_TEXTS_CACHE
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers package is required."
        )

    if _MODEL_CACHE is None:
        _MODEL_CACHE = SentenceTransformer(model_name)
    model = _MODEL_CACHE

    # Cache candidate embeddings (692 vectors take ~40s to compute)
    if _CANDIDATE_EMBEDDINGS_CACHE is None or _CANDIDATE_TEXTS_CACHE != candidate_texts:
        logger.info("Computing candidate embeddings for the first time...")
        _CANDIDATE_EMBEDDINGS_CACHE = model.encode(
            candidate_texts, convert_to_numpy=True, normalize_embeddings=True,
        )
        _CANDIDATE_TEXTS_CACHE = candidate_texts
    
    candidate_embeddings = _CANDIDATE_EMBEDDINGS_CACHE

    # Encode queries (only ~10-15 vectors, takes < 1s)
    query_embeddings = model.encode(
        query_texts, convert_to_numpy=True, normalize_embeddings=True,
    )

    # Cosine similarity
    similarity_matrix = query_embeddings @ candidate_embeddings.T
    return similarity_matrix


def escoxlmr_search(
    concepts: list[str],
    course_context: str,
    metadata_path: str | Path,
    model_name: str = "jjzha/escoxlmr_skill_extraction",
    top_k: int = 50,
) -> list[SupportCandidate]:
    """Tìm kiếm ESCOXLM-R cho support concepts.

    Args:
        concepts: Danh sách support concepts từ Bước 2.
        course_context: Course context (dùng để enrich query).
        metadata_path: Đường dẫn ESCO metadata JSON.
        model_name: ESCOXLM-R checkpoint.
        top_k: Số kết quả tối đa cho mỗi concept.

    Returns:
        Danh sách SupportCandidate (đã dedup theo skill_uri).
    """
    metadata = _load_metadata(metadata_path)

    # Build candidate texts
    candidate_texts = []
    valid_entries = []
    for entry in metadata:
        label = entry.get("skill_label", entry.get("preferred_label", ""))
        desc = entry.get("skill_description", entry.get("description", ""))
        text = f"{label}. {desc}" if desc else label
        if text.strip():
            candidate_texts.append(text)
            valid_entries.append(entry)

    if not candidate_texts:
        logger.warning("No ESCO candidates available for ESCOXLM-R search.")
        return []

    # Build query texts (enriched with context)
    query_texts = [f"{c}. {course_context[:150]}" for c in concepts]

    logger.info(
        "Computing ESCOXLM-R scores: %d queries × %d candidates...",
        len(query_texts), len(candidate_texts),
    )

    similarity_matrix = _compute_escoxlmr_scores(
        query_texts, candidate_texts, model_name,
    )

    # Track best per URI
    best_candidates: dict[str, SupportCandidate] = {}
    # Also track raw score per URI for use in Bước 5
    raw_scores: dict[str, float] = {}

    for q_idx, concept in enumerate(concepts):
        scores = similarity_matrix[q_idx]
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        for rank, idx in enumerate(ranked_indices, start=1):
            entry = valid_entries[idx]
            uri = entry.get("skill_uri", entry.get("uri", entry.get("skill_id", "")))
            score = float(scores[idx])

            candidate = SupportCandidate(
                skill_uri=uri,
                skill_label=entry.get("skill_label", entry.get("preferred_label", "")),
                skill_description=entry.get("skill_description", entry.get("description", "")),
                skill_type=str(entry.get("skill_type", "")).lower(),
                score=score,
                channel="escoxlmr",
                concept_origin=concept,
                rank=rank,
            )

            if uri not in best_candidates or score > best_candidates[uri].score:
                best_candidates[uri] = candidate
                raw_scores[uri] = score

    results = sorted(best_candidates.values(), key=lambda c: c.score, reverse=True)

    logger.info(
        "ESCOXLM-R search: %d concepts → %d unique candidates",
        len(concepts), len(results),
    )
    return results
