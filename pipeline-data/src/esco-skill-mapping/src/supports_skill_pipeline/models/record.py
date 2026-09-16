"""SupportSkillRecord — bản ghi output cuối cùng của pipeline M5.

Đây là object được ghi xuống JSON và nạp vào Knowledge Graph.
Mỗi record đại diện cho 1 quan hệ SUPPORTS_SKILL giữa 1 course và 1 ESCO concept.

Cấu trúc output JSON giống data_teaches_skill/ nhưng với:
- relation_type = "SUPPORTS_SKILL"
- Thêm support_concept_origin (concept thô từ LLM Bước 2)
- review_status từ Human Review (Bước 6)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidenceRef:
    """Tham chiếu tới evidence text đã contribute vào record."""
    source_type: str     # MO_TA, MUC_TIEU, CLO
    source_id: str       # MT1, L1, MAIN
    text: str            # Evidence text
    similarity: float = 0.0  # Cosine similarity với support concept


@dataclass(frozen=True)
class SupportSkillRecord:
    """Bản ghi output chính — ghi xuống JSON, nạp vào KG.

    Chứa đầy đủ thông tin provenance, scoring, evidence
    để có thể giải thích tại sao course X supports skill Y.
    """
    # Course info
    course_code: str
    course_title: str

    # Relation — luôn là SUPPORTS_SKILL
    relation_type: str = "SUPPORTS_SKILL"

    # ESCO concept
    esco_uri: str = ""
    preferred_label: str = ""
    skill_type: str = ""          # "skill/competence" hoặc "knowledge"

    # Support concept origin (từ LLM Bước 2)
    support_concept_origin: str = ""

    # Scores
    rrf_score: float = 0.0
    escoxlmr_score: float = 0.0
    evidence_score: float = 0.0
    final_score: float = 0.0

    # Ranking info
    candidate_rank: int = 0
    bm25_rank: int | None = None
    faiss_rank: int | None = None
    escoxlmr_rank: int | None = None

    # Evidence
    evidence_text: str = ""
    evidence: list[EvidenceRef] = field(default_factory=list)

    # Review
    review_status: str = "pending"  # "pending" / "accepted" / "rejected"

    # LLM Verification
    llm_reasoning: str = ""

    # Metadata
    schema_version: str = "1.0"
    method: str = "LLM-Concept+BM25+FAISS+ESCOXLMR+RRF+MultiSignal"

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dict cho JSON export."""
        return {
            "esco_concept": {
                "uri": self.esco_uri,
                "preferred_label": self.preferred_label,
                "skill_type": self.skill_type,
                "relation_type": self.relation_type,
            },
            "course": {
                "course_code": self.course_code,
                "course_title": self.course_title,
            },
            "support_context": {
                "support_concept_origin": self.support_concept_origin,
                "evidence_text": self.evidence_text,
            },
            "scoring": {
                "final_score": round(self.final_score, 6),
                "rrf_score": round(self.rrf_score, 6),
                "escoxlmr_score": round(self.escoxlmr_score, 6),
                "evidence_score": round(self.evidence_score, 6),
                "candidate_rank": self.candidate_rank,
            },
            "retrieval": {
                "bm25_rank": self.bm25_rank,
                "faiss_rank": self.faiss_rank,
                "escoxlmr_rank": self.escoxlmr_rank,
            },
            "evidence": [
                {
                    "source_type": e.source_type,
                    "source_id": e.source_id,
                    "text": e.text,
                    "similarity": round(e.similarity, 4),
                }
                for e in self.evidence
            ],
            "review_status": self.review_status,
            "llm_reasoning": self.llm_reasoning,
            "method": self.method,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize thành JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
