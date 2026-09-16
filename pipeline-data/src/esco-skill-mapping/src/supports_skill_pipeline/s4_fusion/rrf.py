"""Bước 4 — Reciprocal Rank Fusion (RRF).

Hợp nhất 3 ranking (BM25, FAISS, ESCOXLM-R) thành 1 ranking chung.

Công thức: RRF(d) = Σ 1 / (k + rank_i(d))  với i ∈ {BM25, FAISS, ESCOXLM-R}

Cài đặt thuần Python, không cần thư viện ngoài.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from ..models.candidate import SupportCandidate, FusedCandidate

logger = logging.getLogger(__name__)

DEFAULT_RRF_K = 60


def rrf_fusion(
    bm25_results: list[SupportCandidate],
    faiss_results: list[SupportCandidate],
    escoxlmr_results: list[SupportCandidate],
    k: int = DEFAULT_RRF_K,
    top_n: int = 30,
) -> list[FusedCandidate]:
    """Hợp nhất kết quả từ 3 kênh bằng RRF.

    Args:
        bm25_results: Candidates từ BM25 (Bước 3.1).
        faiss_results: Candidates từ FAISS (Bước 3.2).
        escoxlmr_results: Candidates từ ESCOXLM-R (Bước 3.3).
        k: Hằng số k trong công thức RRF (mặc định 60).
        top_n: Số candidates cuối cùng sau fusion.

    Returns:
        List[FusedCandidate] sắp theo RRF score giảm dần.
        Mỗi skill_uri chỉ xuất hiện 1 lần (dedup).
    """
    # Group candidates by channel, sort by score, assign rank
    channel_data: dict[str, list[SupportCandidate]] = {
        "bm25": sorted(bm25_results, key=lambda c: c.score, reverse=True),
        "faiss": sorted(faiss_results, key=lambda c: c.score, reverse=True),
        "escoxlmr": sorted(escoxlmr_results, key=lambda c: c.score, reverse=True),
    }

    # Tính RRF score cho mỗi URI
    rrf_scores: dict[str, float] = defaultdict(float)
    channel_ranks: dict[str, dict[str, int]] = defaultdict(lambda: {})
    concept_origins: dict[str, set[str]] = defaultdict(set)
    best_metadata: dict[str, SupportCandidate] = {}
    escoxlmr_raw_scores: dict[str, float] = {}

    for channel_name, candidates in channel_data.items():
        # Dedup per channel (giữ score cao nhất per URI)
        seen_uris: dict[str, int] = {}
        rank = 0

        for cand in candidates:
            uri = cand.skill_uri
            if uri in seen_uris:
                continue

            rank += 1
            seen_uris[uri] = rank

            # RRF score contribution
            rrf_scores[uri] += 1.0 / (k + rank)

            # Track metadata
            channel_ranks[uri][channel_name] = rank
            if cand.concept_origin:
                concept_origins[uri].add(cand.concept_origin)

            # Keep best metadata
            if uri not in best_metadata or cand.score > best_metadata[uri].score:
                best_metadata[uri] = cand

            # Track ESCOXLM-R raw score for Bước 5
            if channel_name == "escoxlmr":
                escoxlmr_raw_scores[uri] = cand.score

    # Sort by RRF score, build FusedCandidate
    sorted_uris = sorted(
        rrf_scores.keys(),
        key=lambda u: rrf_scores[u],
        reverse=True,
    )[:top_n]

    fused: list[FusedCandidate] = []

    for uri in sorted_uris:
        meta = best_metadata[uri]
        ranks = channel_ranks[uri]

        fused.append(FusedCandidate(
            skill_uri=uri,
            skill_label=meta.skill_label,
            skill_description=meta.skill_description,
            skill_type=meta.skill_type,
            rrf_score=rrf_scores[uri],
            concept_origins=sorted(concept_origins[uri]),
            bm25_rank=ranks.get("bm25"),
            faiss_rank=ranks.get("faiss"),
            escoxlmr_rank=ranks.get("escoxlmr"),
            escoxlmr_score=escoxlmr_raw_scores.get(uri, 0.0),
        ))

    logger.info(
        "RRF fusion: BM25=%d + FAISS=%d + ESCOXLMR=%d → %d fused (top-%d), k=%d",
        len(bm25_results), len(faiss_results), len(escoxlmr_results),
        len(fused), top_n, k,
    )

    return fused
