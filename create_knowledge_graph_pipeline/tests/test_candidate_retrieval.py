"""Tests for high-recall ESCO candidate retrieval contracts."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.skill_matching.candidate_retrieval import CandidateRetriever


class _Model:
    def encode(self, texts: list[str], **_: object) -> np.ndarray:
        return np.asarray([[1.0, 0.0] for _ in texts], dtype=float)


class _Pool:
    def __init__(self) -> None:
        self.model = _Model()
        self.embeddings = np.asarray([[1.0, 0.0]], dtype=float)
        skill = SimpleNamespace(
            skill_id="S1",
            skill_uri="esco:S1",
            skill_label="perform calculations",
            skill_description="Perform mathematical calculations.",
        )
        self.skills = [skill]
        self.by_uri = {skill.skill_uri: skill}

    def score_candidates(self, texts: list[str], uris: list[list[str]], batch_size: int) -> list[dict[str, float]]:
        del texts, batch_size
        return [{uri: 1.0 for uri in row} for row in uris]


def test_retrieval_uses_context_text_and_records_rank() -> None:
    config = SimpleNamespace(
        retrieval_query_types=("lesson",),
        retrieval_top_k=20,
        retrieval_threshold=0.3,
        embedding_batch_size=8,
    )
    query = {
        "course_id": "C1",
        "query_id": "lesson:L1",
        "query_type": "lesson",
        "retrieval_text_en": "Calculus > Double Integrals > Work and Force",
        "evidence_text_en": "Work and Force",
        "source_unit_ids": ["L1"],
        "source_unit_types": ["lesson"],
    }

    candidates = CandidateRetriever(config).retrieve([query], _Pool())

    assert len(candidates) == 1
    assert candidates[0]["retrieval_rank"] == 1
    assert candidates[0]["retrieval_text_en"] == query["retrieval_text_en"]
    assert candidates[0]["evidence_text_en"] == query["evidence_text_en"]

