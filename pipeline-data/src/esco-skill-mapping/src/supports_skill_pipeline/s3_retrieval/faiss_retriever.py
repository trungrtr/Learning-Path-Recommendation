"""Bước 3.2 — FAISS Semantic Retrieval (general-purpose).

Tìm kiếm semantic bằng embedding vectors trong FAISS index.
Support concepts và course context được encode bằng Sentence-Transformers,
sau đó tìm top-k nearest neighbors trong ESCO pool.

Công nghệ: Sentence-Transformers + FAISS.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from ..models.candidate import SupportCandidate

logger = logging.getLogger(__name__)


_FAISS_INDEX_CACHE: Any = None
_METADATA_CACHE: list[dict[str, Any]] | None = None
_MODEL_CACHE: Any = None

def _load_faiss_index(index_path: str | Path):
    global _FAISS_INDEX_CACHE
    if _FAISS_INDEX_CACHE is not None:
        return _FAISS_INDEX_CACHE
        
    try:
        import faiss
    except ImportError:
        raise ImportError("faiss-cpu package is required. Install with: pip install faiss-cpu")

    path = Path(index_path)
    if not path.exists():
        raise FileNotFoundError(f"FAISS index not found: {path}")

    index = faiss.read_index(str(path))
    logger.info("Loaded FAISS index: %d vectors, dim=%d", index.ntotal, index.d)
    _FAISS_INDEX_CACHE = index
    return index


def _load_metadata(metadata_path: str | Path) -> list[dict[str, Any]]:
    global _METADATA_CACHE
    if _METADATA_CACHE is not None:
        return _METADATA_CACHE
        
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        _METADATA_CACHE = json.load(f)
    return _METADATA_CACHE


def _encode_texts(texts: list[str], model_name: str) -> np.ndarray:
    global _MODEL_CACHE
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError(
            "sentence-transformers package is required. "
            "Install with: pip install sentence-transformers"
        )

    if _MODEL_CACHE is None:
        _MODEL_CACHE = SentenceTransformer(model_name)
        
    model = _MODEL_CACHE
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings


def faiss_search(
    concepts: list[str],
    course_context: str,
    faiss_index_path: str | Path,
    metadata_path: str | Path,
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    top_k: int = 50,
) -> list[SupportCandidate]:
    """Tìm kiếm semantic FAISS cho support concepts.

    Args:
        concepts: Danh sách support concepts từ Bước 2.
        course_context: Course context đã chuẩn hóa (từ Bước 1).
        faiss_index_path: Đường dẫn FAISS index file.
        metadata_path: Đường dẫn ESCO metadata JSON.
        embedding_model: Tên model Sentence-Transformers.
        top_k: Số kết quả tối đa cho mỗi query.

    Returns:
        Danh sách SupportCandidate (đã dedup theo skill_uri).
    """
    index = _load_faiss_index(faiss_index_path)
    metadata = _load_metadata(metadata_path)

    # Tạo query texts: mỗi concept + course context (để bổ sung ngữ cảnh)
    query_texts = []
    query_concepts = []
    for concept in concepts:
        # Query = concept enriched with course context snippet
        query = f"{concept}. {course_context[:200]}"
        query_texts.append(query)
        query_concepts.append(concept)

    # Encode queries
    query_embeddings = _encode_texts(query_texts, embedding_model)

    # Search FAISS
    distances, indices = index.search(
        query_embeddings.astype(np.float32),
        min(top_k, index.ntotal),
    )

    # Track best per URI
    best_candidates: dict[str, SupportCandidate] = {}

    for q_idx in range(len(query_texts)):
        concept = query_concepts[q_idx]

        for rank, (dist, meta_idx) in enumerate(
            zip(distances[q_idx], indices[q_idx]), start=1
        ):
            if meta_idx < 0 or meta_idx >= len(metadata):
                continue

            entry = metadata[meta_idx]
            uri = entry.get("skill_uri", entry.get("uri", entry.get("skill_id", "")))

            # FAISS inner product distance → similarity score
            score = float(dist)

            candidate = SupportCandidate(
                skill_uri=uri,
                skill_label=entry.get("skill_label", entry.get("preferred_label", "")),
                skill_description=entry.get("skill_description", entry.get("description", "")),
                skill_type=str(entry.get("skill_type", "")).lower(),
                score=score,
                channel="faiss",
                concept_origin=concept,
                rank=rank,
            )

            if uri not in best_candidates or candidate.score > best_candidates[uri].score:
                best_candidates[uri] = candidate

    results = sorted(best_candidates.values(), key=lambda c: c.score, reverse=True)

    logger.info(
        "FAISS search: %d concepts → %d unique candidates",
        len(concepts), len(results),
    )
    return results
