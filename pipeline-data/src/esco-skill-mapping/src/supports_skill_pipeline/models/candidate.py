"""Candidate models — ứng viên ESCO ở các giai đoạn pipeline M5.

SupportCandidate: sau Bước 3 (retrieval) — 1 kênh duy nhất.
FusedCandidate: sau Bước 4 (RRF fusion).
ScoredCandidate: sau Bước 5 (multi-signal ranking).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SupportCandidate:
    """Ứng viên ESCO từ 1 kênh retrieval duy nhất.

    Attributes:
        skill_uri: URI ESCO gốc.
        skill_label: Preferred label ESCO.
        skill_description: Mô tả ESCO.
        skill_type: "skill/competence" hoặc "knowledge" (từ ESCO metadata).
        score: Điểm từ kênh cụ thể.
        channel: Kênh sinh ra candidate ("bm25" / "faiss" / "escoxlmr").
        concept_origin: Support concept (từ Bước 2) đã sinh ra candidate này.
        rank: Thứ hạng trong kênh.
    """
    skill_uri: str
    skill_label: str
    skill_description: str
    skill_type: str
    score: float
    channel: str  # "bm25" / "faiss" / "escoxlmr"
    concept_origin: str = ""
    rank: int = 0


@dataclass
class FusedCandidate:
    """Ứng viên đã qua RRF fusion (3 kênh).

    Attributes:
        skill_uri: URI ESCO gốc.
        skill_label: Preferred label ESCO.
        skill_description: Mô tả ESCO.
        skill_type: "skill/competence" hoặc "knowledge".
        rrf_score: Điểm RRF tổng hợp.
        concept_origins: Danh sách support concepts đã sinh ra candidate.
        bm25_rank: Rank từ BM25 (None nếu không có).
        faiss_rank: Rank từ FAISS (None nếu không có).
        escoxlmr_rank: Rank từ ESCOXLM-R (None nếu không có).
        escoxlmr_score: Điểm raw từ ESCOXLM-R (để dùng ở Bước 5).
    """
    skill_uri: str
    skill_label: str
    skill_description: str
    skill_type: str
    rrf_score: float = 0.0
    concept_origins: list[str] = field(default_factory=list)
    bm25_rank: int | None = None
    faiss_rank: int | None = None
    escoxlmr_rank: int | None = None
    escoxlmr_score: float = 0.0

    @property
    def skill_id(self) -> str:
        """Trích xuất ID ngắn từ URI."""
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]


@dataclass
class ScoredCandidate:
    """Ứng viên sau Multi-signal Ranking (Bước 5) — sẵn sàng cho Human Review.

    Attributes:
        skill_uri: URI ESCO gốc.
        skill_label: Preferred label ESCO.
        skill_description: Mô tả ESCO.
        skill_type: "skill/competence" hoặc "knowledge".
        rrf_score: Điểm RRF.
        escoxlmr_score: Điểm ESCOXLM-R.
        evidence_score: Điểm evidence (cosine similarity cao nhất).
        final_score: Điểm tổng hợp = α·RRF + β·ESCOXLMR + γ·Evidence.
        evidence_text: Câu evidence có similarity cao nhất.
        concept_origins: Support concepts gốc.
        bm25_rank: Rank từ BM25.
        faiss_rank: Rank từ FAISS.
        escoxlmr_rank: Rank từ ESCOXLM-R.
        candidate_rank: Rank cuối cùng sau scoring.
        review_status: "pending" / "accepted" / "rejected".
    """
    skill_uri: str
    skill_label: str
    skill_description: str
    skill_type: str
    rrf_score: float = 0.0
    escoxlmr_score: float = 0.0
    evidence_score: float = 0.0
    final_score: float = 0.0
    evidence_text: str = ""
    concept_origins: list[str] = field(default_factory=list)
    bm25_rank: int | None = None
    faiss_rank: int | None = None
    escoxlmr_rank: int | None = None
    candidate_rank: int = 0
    review_status: str = "pending"
    llm_reasoning: str = ""

    @property
    def skill_id(self) -> str:
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]
