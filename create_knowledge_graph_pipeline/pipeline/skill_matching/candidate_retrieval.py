"""Bước B: retrieval nội bộ, tái hiện ESCO extractor trên vocabulary ESCO IT-30 đóng."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from .models import SkillCandidate
from .config import SkillMatchingConfig
from .skill_pool import SkillPool

LOGGER = logging.getLogger(__name__)


class CandidateRetriever:
    """Sinh URI ứng viên bằng cosine retrieval trên ESCO IT-30 được lưu trong project."""

    def __init__(self, config: SkillMatchingConfig) -> None:
        self.config = config

    def _retrieve_uris(self, texts: list[str], pool: SkillPool) -> list[list[str]]:
        """Lấy top-K ESCO skill gần nhất cho từng direct/ability query bằng cosine similarity."""
        if not texts:
            return []
        phrase_embeddings = pool.model.encode(
            texts,
            batch_size=self.config.embedding_batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        scores = phrase_embeddings @ pool.embeddings.T
        top_k = min(self.config.retrieval_top_k, len(pool.skills))
        sorted_indices = scores.argsort(axis=1)[:, ::-1][:, :top_k]
        return [
            [
                pool.skills[int(index)].skill_uri
                for index in indices
                if float(row_scores[int(index)]) >= self.config.retrieval_threshold
            ]
            for row_scores, indices in zip(scores, sorted_indices)
        ]

    def retrieve(self, queries: Iterable[dict[str, Any]], pool: SkillPool) -> list[dict[str, Any]]:
        """Sinh ứng viên URI từ query records và giữ đầy đủ provenance cho tầng aggregate."""
        valid_queries = [
            query
            for query in queries
            if query.get("query_type") in self.config.retrieval_query_types
            and isinstance(query.get("retrieval_text_en"), str)
            and query["retrieval_text_en"].strip()
        ]
        if not valid_queries:
            return []
        texts = [query["retrieval_text_en"] for query in valid_queries]
        candidate_uris = self._retrieve_uris(texts, pool)
        cosine_scores = pool.score_candidates(texts, candidate_uris, self.config.embedding_batch_size)

        candidates: list[dict[str, Any]] = []
        for query, uris, scores in zip(valid_queries, candidate_uris, cosine_scores):
            for rank, skill_uri in enumerate(uris, start=1):
                skill = pool.by_uri.get(skill_uri)
                if skill is None:
                    # Vocabulary của ESCOX phải khớp IT-30 pool; bỏ URI ngoài pool để giữ ground truth đóng.
                    LOGGER.warning("Bỏ qua URI không có trong ESCO IT-30 pool: %s", skill_uri)
                    continue
                candidates.append(
                    SkillCandidate.model_validate(
                        {
                            "course_id": query["course_id"],
                            "query_id": query["query_id"],
                            "query_type": query["query_type"],
                            "source_unit_ids": query["source_unit_ids"],
                            "source_unit_types": query["source_unit_types"],
                            "retrieval_text_en": query["retrieval_text_en"],
                            "evidence_text_en": query["evidence_text_en"],
                            "chunk_index": query.get("chunk_index"),
                            "skill_id": skill.skill_id,
                            "skill_uri": skill.skill_uri,
                            "skill_label": skill.skill_label,
                            "skill_description": skill.skill_description,
                            "retrieval_rank": rank,
                            "retrieval_score": scores.get(skill.skill_uri),
                        }
                    ).model_dump(exclude_none=True)
                )
        return candidates
