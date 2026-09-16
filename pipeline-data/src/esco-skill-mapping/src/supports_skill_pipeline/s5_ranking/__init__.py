"""Bước 5 — Multi-signal Ranking."""

from .evidence_scorer import compute_evidence
from .multi_signal import rank_candidates

__all__ = ["compute_evidence", "rank_candidates"]
