"""Candidate models — ứng viên ESCO ở các giai đoạn pipeline.

RetrievalCandidate: sau Tầng 2 (matching) — 1 kênh duy nhất.
FusedCandidate: sau Tầng 3 (RRF fusion) + Tầng 4 (rerank).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .enums import ConceptType, RetrievalChannel, ExtractionSource, HeadType


@dataclass
class RetrievalCandidate:
    """Ứng viên ESCO từ 1 kênh retrieval duy nhất (BM25 hoặc Dense).

    Attributes:
        skill_uri: URI ESCO gốc.
        skill_label: Preferred label ESCO.
        skill_description: Mô tả ESCO.
        concept_type: "skill" hoặc "knowledge" (từ ESCO metadata).
        score: Điểm từ kênh cụ thể (chưa chuẩn hóa).
        channel: Kênh sinh ra candidate (bm25 / dense / esco_extract).
        evidence_id: ID evidence đã dùng để tìm.
        mention_text: Text mention gốc (từ Tầng 1).
        source_text: Text evidence gốc (cho reranker).
        extraction_source: Model nào đã sinh mention ban đầu.
        head_type: skill head hay knowledge head (từ ESCOXLM-R).
    """
    skill_uri: str
    skill_label: str
    skill_description: str
    concept_type: ConceptType
    score: float
    channel: RetrievalChannel
    evidence_id: str = ""
    mention_text: str = ""
    source_text: str = ""
    extraction_source: ExtractionSource | None = None
    head_type: HeadType | None = None
    rank: int = 1

    @property
    def skill_id(self) -> str:
        """Trích xuất ID ngắn từ URI."""
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]


@dataclass
class FusedCandidate:
    """Ứng viên đã qua RRF merge (nhiều kênh) và/hoặc rerank.

    Attributes:
        skill_uri: URI ESCO gốc.
        skill_label: Preferred label ESCO.
        skill_description: Mô tả ESCO.
        concept_type: "skill" hoặc "knowledge".
        score_rrf: Điểm RRF tổng hợp.
        score_rerank: Điểm Cross-Encoder (None nếu chưa rerank).
        combined_score: Điểm tổng hợp cuối cùng.
        evidence_ids: Danh sách evidence_id đã contribute.
        source_texts: Danh sách evidence text tương ứng.
        mention_texts: Danh sách mention text đã tìm ra candidate này.
        extraction_sources: Nguồn extraction cho mỗi evidence.
        head_types: Head type cho mỗi evidence (skill/knowledge).
        bm25_rank: Rank từ BM25 (None nếu không có).
        dense_rank: Rank từ Dense (None nếu không có).
        esco_extract_rank: Rank từ esco-extract-skill (None nếu không có).
    """
    skill_uri: str
    skill_label: str
    skill_description: str
    concept_type: ConceptType
    score_rrf: float = 0.0
    score_rerank: float | None = None
    combined_score: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    source_texts: list[str] = field(default_factory=list)
    mention_texts: list[str] = field(default_factory=list)
    extraction_sources: list[ExtractionSource] = field(default_factory=list)
    head_types: list[HeadType | None] = field(default_factory=list)
    bm25_rank: int | None = None
    dense_rank: int | None = None
    esco_extract_rank: int | None = None
    # [PATCH v3.0 — Retrieval Agreement & Low Evidence Quality]
    # Lý do: Lưu trữ độ đồng thuận truy xuất kênh và cờ chất lượng bằng chứng kém
    # Ảnh hưởng: models/candidate.py, t3_fusion, t5_decision, pipeline.py
    retrieval_agreement: str = "PARTIAL"
    low_evidence_quality: bool = False

    @property
    def skill_id(self) -> str:
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]
