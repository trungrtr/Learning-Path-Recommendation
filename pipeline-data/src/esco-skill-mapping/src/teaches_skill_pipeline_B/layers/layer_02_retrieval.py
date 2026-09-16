"""Layer 02 — Retrieval: FAISS + BM25 + RRF Fusion.

Kết hợp kết quả từ Semantic Search (Dense) và Keyword Search (Sparse).
Sử dụng Reciprocal Rank Fusion (RRF) để hợp nhất kết quả.
"""

from __future__ import annotations

import json
import logging
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..models.schemas import RawMention, RetrievalCandidate, FusedCandidate, DirectCandidate

logger = logging.getLogger(__name__)

DEFAULT_RRF_K = 60

# --- Agreement & Fusion Logic ---

def compute_retrieval_agreement(bm25_rank: int | None, dense_rank: int | None) -> str:
    if bm25_rank is None or dense_rank is None:
        return "SINGLE_RETRIEVER"
    if bm25_rank <= 5 and dense_rank <= 5:
        return "STRONG"
    if bm25_rank > 15 and dense_rank > 15:
        return "WEAK"
    return "PARTIAL"

def reciprocal_rank_fusion(
    channel_results: dict[str, list[RetrievalCandidate]],
    direct_candidates: list[DirectCandidate] | None = None,
    rrf_k: int = DEFAULT_RRF_K,
    top_k: int = 100,
) -> list[FusedCandidate]:
    evidence_groups: dict[str, dict[str, list[RetrievalCandidate]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for channel, cands in channel_results.items():
        for c in cands:
            evidence_groups[c.evidence_id][channel].append(c)

    if direct_candidates:
        for dc in direct_candidates:
            rc = RetrievalCandidate(
                skill_uri=dc.skill_uri,
                skill_label=dc.skill_label,
                skill_description="",
                concept_type="skill",
                score=dc.score,
                channel="esco_extract",
                evidence_id=dc.evidence_id,
            )
            evidence_groups[dc.evidence_id]["esco_extract"].append(rc)

    global_scores: dict[str, float] = defaultdict(float)
    global_best: dict[str, RetrievalCandidate] = {}
    global_evidence: dict[str, list[str]] = defaultdict(list)
    global_sources: dict[str, list[str]] = defaultdict(list)
    global_mentions: dict[str, list[str]] = defaultdict(list)
    global_evidence_mentions: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    global_ranks: dict[str, dict[str, int | None]] = defaultdict(lambda: {
        "bm25": None, "dense": None, "esco_extract": None,
        "bm25_ctx": None, "dense_ctx": None,
    })

    for eid, channels in evidence_groups.items():
        for channel, cands in channels.items():
            best_cand_per_uri: dict[str, RetrievalCandidate] = {}
            for c in cands:
                if c.skill_uri not in best_cand_per_uri or c.score > best_cand_per_uri[c.skill_uri].score:
                    best_cand_per_uri[c.skill_uri] = c

            sorted_cands = sorted(best_cand_per_uri.values(), key=lambda c: c.score, reverse=True)

            for rank, cand in enumerate(sorted_cands, start=1):
                uri = cand.skill_uri
                rrf_score = 1.0 / (rrf_k + rank)
                global_scores[uri] += rrf_score

                if uri not in global_best or cand.score > global_best[uri].score:
                    global_best[uri] = cand

                if eid not in global_evidence[uri]:
                    global_evidence[uri].append(eid)
                if cand.mention_text and cand.mention_text not in global_mentions[uri]:
                    global_mentions[uri].append(cand.mention_text)
                if cand.mention_text and cand.mention_text not in global_evidence_mentions[uri][eid]:
                    global_evidence_mentions[uri][eid].append(cand.mention_text)
                if cand.extraction_source and cand.extraction_source not in global_sources[uri]:
                    global_sources[uri].append(cand.extraction_source)

                cand_query_rank = getattr(cand, "rank", rank)
                current = global_ranks[uri].get(channel)
                if current is None or cand_query_rank < current:
                    global_ranks[uri][channel] = cand_query_rank

    sorted_uris = sorted(
        global_scores.keys(),
        key=lambda u: global_scores[u],
        reverse=True,
    )[:top_k]

    fused: list[FusedCandidate] = []
    for rrf_rank, uri in enumerate(sorted_uris, start=1):
        best = global_best[uri]
        ranks = global_ranks[uri]
        agreement = compute_retrieval_agreement(ranks.get("bm25"), ranks.get("dense"))

        fused.append(FusedCandidate(
            skill_uri=uri,
            skill_label=best.skill_label,
            skill_description=best.skill_description,
            concept_type=best.concept_type,
            score_rrf=global_scores[uri],
            evidence_ids=global_evidence[uri],
            source_texts=[best.source_text] if best.source_text else [],
            mention_texts=global_mentions[uri],
            evidence_mentions=dict(global_evidence_mentions[uri]),
            extraction_sources=global_sources[uri],
            head_types=[best.head_type] if best.head_type else [],
            bm25_rank=ranks.get("bm25"),
            dense_rank=ranks.get("dense"),
            esco_extract_rank=ranks.get("esco_extract"),
            retrieval_agreement=agreement,
        ))

    return fused


# --- Matchers ---

class DenseMatcher:
    def __init__(self, index_path: str | Path, metadata_path: str | Path, embedding_model: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"):
        self._index_path = Path(index_path)
        self._metadata_path = Path(metadata_path)
        self._embedding_model_name = embedding_model
        self._index: Any = None
        self._metadata: list[dict] = []
        self._encoder: Any = None

    def _load(self) -> None:
        if self._index is not None:
            return
        import faiss
        from sentence_transformers import SentenceTransformer
        self._index = faiss.read_index(str(self._index_path))
        with open(self._metadata_path, encoding="utf-8") as f:
            self._metadata = json.load(f)
        self._encoder = SentenceTransformer(self._embedding_model_name)

    def match(self, mentions: list[RawMention], top_k: int = 50) -> list[RetrievalCandidate]:
        self._load()
        if not mentions:
            return []
        candidates = self._match_pass(mentions, top_k, "dense", lambda m: m.text)
        candidates += self._match_pass(mentions, top_k, "dense_ctx", lambda m: f"{m.text}. Context: {m.source_text}" if m.source_text else m.text)
        return candidates

    def _match_pass(self, mentions: list[RawMention], top_k: int, channel: str, text_fn) -> list[RetrievalCandidate]:
        texts = [text_fn(m) for m in mentions]
        embeddings = self._encoder.encode(texts, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        distances, indices = self._index.search(embeddings, top_k)

        candidates: list[RetrievalCandidate] = []
        for i, mention in enumerate(mentions):
            for j in range(top_k):
                idx = int(indices[i][j])
                if idx < 0 or idx >= len(self._metadata):
                    continue
                score = float(distances[i][j])
                meta = self._metadata[idx]
                candidates.append(RetrievalCandidate(
                    skill_uri=meta.get("skill_uri", ""),
                    skill_label=meta.get("skill_label", ""),
                    skill_description=meta.get("skill_description", ""),
                    concept_type="knowledge" if "knowledge" in str(meta.get("skill_type", "")).lower() else "skill",
                    score=score,
                    channel=channel,
                    evidence_id=mention.evidence_id,
                    mention_text=mention.text,
                    source_text=mention.source_text,
                    extraction_source=mention.source,
                    head_type=mention.head_type,
                    rank=j + 1,
                ))
        return candidates


class BM25Matcher:
    def __init__(self, index_path: str | Path, metadata_path: str | Path):
        self._index_path = Path(index_path)
        self._metadata_path = Path(metadata_path)
        self._bm25: Any = None
        self._metadata: list[dict] = []

    def _load(self) -> None:
        if self._bm25 is not None:
            return
        with open(self._index_path, "rb") as f:
            self._bm25 = pickle.load(f)
        with open(self._metadata_path, encoding="utf-8") as f:
            self._metadata = json.load(f)

    def match(self, mentions: list[RawMention], top_k: int = 50) -> list[RetrievalCandidate]:
        self._load()
        candidates: list[RetrievalCandidate] = []
        for mention in mentions:
            candidates += self._match_one(mention, top_k, "bm25", mention.text)
            ctx = f"{mention.text} {mention.source_text}" if mention.source_text else mention.text
            candidates += self._match_one(mention, top_k, "bm25_ctx", ctx)
        return candidates

    def _match_one(self, mention: RawMention, top_k: int, channel: str, query_text: str) -> list[RetrievalCandidate]:
        query_tokens = query_text.lower().split()
        if not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        candidates: list[RetrievalCandidate] = []
        for rank, idx in enumerate(top_indices, start=1):
            if scores[idx] <= 0:
                continue
            meta = self._metadata[idx]
            candidates.append(RetrievalCandidate(
                skill_uri=meta.get("skill_uri", ""),
                skill_label=meta.get("skill_label", ""),
                skill_description=meta.get("skill_description", ""),
                concept_type="knowledge" if "knowledge" in str(meta.get("skill_type", "")).lower() else "skill",
                score=float(scores[idx]),
                channel=channel,
                evidence_id=mention.evidence_id,
                mention_text=mention.text,
                source_text=mention.source_text,
                extraction_source=mention.source,
                head_type=mention.head_type,
                rank=rank,
            ))
        return candidates

# --- Retrieval Layer Wrapper ---

class RetrievalLayer:
    """Tích hợp dense matcher, sparse matcher và RRF fusion."""

    def __init__(self, config: Any):
        self.config = config
        
        # Paths 
        bm25_path = getattr(config.retrieval, "bm25_index_path", "models/bm25_index.pkl")
        faiss_path = getattr(config.retrieval, "faiss_index_path", "models/faiss_index.bin")
        meta_path = getattr(config.retrieval, "faiss_metadata_path", "models/esco_metadata.json")
        dense_model = getattr(config.retrieval, "dense_model_name", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
        
        self.bm25_matcher = BM25Matcher(index_path=bm25_path, metadata_path=meta_path)
        self.dense_matcher = DenseMatcher(index_path=faiss_path, metadata_path=meta_path, embedding_model=dense_model)
        
    def run(self, mentions: list[RawMention], direct_candidates: list[DirectCandidate] | None = None) -> list[FusedCandidate]:
        logger.info("Layer 02 (Retrieval): Processing %d mentions", len(mentions))
        
        top_k = getattr(self.config.retrieval, "top_k", 50)
        rrf_k = getattr(self.config.retrieval, "rrf_k", 60)
        fusion_top_k = getattr(self.config.retrieval, "top_k_per_channel", 100)
        
        # Match
        bm25_cands = self.bm25_matcher.match(mentions, top_k=top_k)
        dense_cands = self.dense_matcher.match(mentions, top_k=top_k)
        
        channel_results = {
            "bm25": bm25_cands,
            "dense": dense_cands
        }
        
        # Merge RRF
        fused = reciprocal_rank_fusion(
            channel_results=channel_results,
            direct_candidates=direct_candidates,
            rrf_k=rrf_k,
            top_k=fusion_top_k
        )
        
        return fused
