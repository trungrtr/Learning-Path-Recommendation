"""Evidence Scorer — tính EvidenceScore cho mỗi candidate.

Với mỗi candidate, tính cosine similarity giữa support_concept
và từng câu trong Description/Objectives/CLO.
Trả về câu có similarity cao nhất làm evidence text + điểm.

Công nghệ: Sentence-Transformers (cùng model embedding ở Bước 3.2).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def _split_into_sentences(text: str) -> list[str]:
    """Tách text thành các câu đơn giản."""
    import re
    # Split by period, newline, or semicolon
    sentences = re.split(r"[.\n;]+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


_MODEL_CACHE: Any = None

def compute_evidence(
    concept_origins: list[str],
    course_context: str,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
) -> list[tuple[str, float]]:
    global _MODEL_CACHE
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers package is required."
        )

    sentences = _split_into_sentences(course_context)
    if not sentences or not concept_origins:
        return [("", 0.0)]

    if _MODEL_CACHE is None:
        _MODEL_CACHE = SentenceTransformer(embedding_model)
    model = _MODEL_CACHE

    sent_embeddings = model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    concept_embeddings = model.encode(concept_origins, convert_to_numpy=True, normalize_embeddings=True)

    sim_matrix = concept_embeddings @ sent_embeddings.T

    results: list[tuple[str, float]] = []
    for c_idx in range(len(concept_origins)):
        best_sent_idx = int(np.argmax(sim_matrix[c_idx]))
        best_score = float(sim_matrix[c_idx, best_sent_idx])
        results.append((sentences[best_sent_idx], best_score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def compute_candidate_evidence(
    concept_origins: list[str],
    course_context: str,
    _model=None,
    _sent_embeddings=None,
    _sentences=None,
) -> tuple[str, float]:
    global _MODEL_CACHE
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError("sentence-transformers package is required.")

    sentences = _sentences or _split_into_sentences(course_context)
    if not sentences or not concept_origins:
        return ("", 0.0)

    if _model is not None:
        model = _model
    else:
        if _MODEL_CACHE is None:
            _MODEL_CACHE = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
        model = _MODEL_CACHE

    if _sent_embeddings is None:
        sent_embeddings = model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    else:
        sent_embeddings = _sent_embeddings

    concept_embeddings = model.encode(concept_origins, convert_to_numpy=True, normalize_embeddings=True)
    sim_matrix = concept_embeddings @ sent_embeddings.T

    best_concept_idx = int(np.max(sim_matrix, axis=1).argmax())
    best_sent_idx = int(np.argmax(sim_matrix[best_concept_idx]))
    best_score = float(sim_matrix[best_concept_idx, best_sent_idx])

    avg_score = float(np.mean(np.max(sim_matrix, axis=1)))
    return (sentences[best_sent_idx], avg_score)
