"""Bước 3.1 — BM25 Lexical Retrieval.

Tìm kiếm từ khóa (lexical) trong Filtered ESCO Pool bằng BM25.
Mỗi support_concept được dùng làm query để tìm skill tương ứng.

Công nghệ: rank_bm25 (standalone, không cần Elasticsearch).
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

from ..models.candidate import SupportCandidate

logger = logging.getLogger(__name__)


def _load_esco_metadata(metadata_path: str | Path) -> list[dict[str, Any]]:
    """Load ESCO metadata từ JSON file."""
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"ESCO metadata not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_bm25_corpus(
    esco_pool: list[dict[str, Any]],
) -> tuple[Any, list[dict[str, Any]]]:
    """Build BM25 index từ ESCO pool.

    Mỗi document = preferred_label + alt_labels + description.
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        raise ImportError(
            "rank_bm25 package is required. Install with: pip install rank-bm25"
        )

    tokenized_corpus = []
    valid_entries = []

    for entry in esco_pool:
        # Build document text từ nhiều fields
        parts = [entry.get("skill_label", entry.get("preferred_label", ""))]
        alt_labels = entry.get("alt_labels", [])
        if isinstance(alt_labels, list):
            parts.extend(alt_labels)
        parts.append(entry.get("skill_description", entry.get("description", "")))

        doc_text = " ".join(p for p in parts if p).lower()
        tokens = doc_text.split()

        if tokens:
            tokenized_corpus.append(tokens)
            valid_entries.append(entry)

    bm25 = BM25Okapi(tokenized_corpus)
    return bm25, valid_entries


def _load_or_build_bm25(
    bm25_index_path: str | Path,
    metadata_path: str | Path,
) -> tuple[Any, list[dict[str, Any]]]:
    """Load BM25 index từ pickle hoặc build mới từ metadata."""
    pkl_path = Path(bm25_index_path)

    if pkl_path.exists():
        try:
            with open(pkl_path, "rb") as f:
                data = pickle.load(f)
            if isinstance(data, dict) and "bm25" in data and "entries" in data:
                logger.info("Loaded BM25 index from %s", pkl_path)
                return data["bm25"], data["entries"]
        except Exception as e:
            logger.warning("Failed to load BM25 pickle: %s — rebuilding.", e)

    # Build mới
    esco_pool = _load_esco_metadata(metadata_path)
    bm25, entries = _build_bm25_corpus(esco_pool)
    logger.info("Built BM25 index with %d entries", len(entries))
    return bm25, entries


def bm25_search(
    concepts: list[str],
    bm25_index_path: str | Path,
    metadata_path: str | Path,
    top_k: int = 50,
) -> list[SupportCandidate]:
    """Tìm kiếm BM25 cho danh sách support concepts.

    Args:
        concepts: Danh sách support concepts từ Bước 2.
        bm25_index_path: Đường dẫn BM25 pickle index.
        metadata_path: Đường dẫn ESCO metadata JSON.
        top_k: Số kết quả tối đa cho mỗi concept.

    Returns:
        Danh sách SupportCandidate (đã dedup theo skill_uri, giữ score cao nhất).
    """
    bm25, entries = _load_or_build_bm25(bm25_index_path, metadata_path)

    # Track best score per URI across all concepts
    best_candidates: dict[str, SupportCandidate] = {}

    for concept in concepts:
        query_tokens = concept.lower().split()
        scores = bm25.get_scores(query_tokens)

        # Get top-k indices
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        for rank, idx in enumerate(ranked_indices, start=1):
            if scores[idx] <= 0:
                continue

            entry = entries[idx]
            uri = entry.get("skill_uri", entry.get("uri", entry.get("skill_id", "")))

            candidate = SupportCandidate(
                skill_uri=uri,
                skill_label=entry.get("skill_label", entry.get("preferred_label", "")),
                skill_description=entry.get("skill_description", entry.get("description", "")),
                skill_type=str(entry.get("skill_type", "")).lower(),
                score=float(scores[idx]),
                channel="bm25",
                concept_origin=concept,
                rank=rank,
            )

            # Giữ candidate có score cao nhất cho mỗi URI
            if uri not in best_candidates or candidate.score > best_candidates[uri].score:
                best_candidates[uri] = candidate

    results = sorted(best_candidates.values(), key=lambda c: c.score, reverse=True)

    logger.info(
        "BM25 search: %d concepts → %d unique candidates",
        len(concepts), len(results),
    )
    return results
