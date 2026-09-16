"""SkillTeacherRecord — bản ghi output cuối cùng của pipeline.

Đây là object được ghi xuống JSON và nạp vào Knowledge Graph.
Mỗi record đại diện cho 1 quan hệ TEACHES_SKILL hoặc TEACHES_KNOWLEDGE
giữa 1 course và 1 ESCO concept.

Cập nhật v3:
- Thêm extraction block (source, head_type, esco_type_agrees)
- Thêm retrieval block (bm25_rank, dense_rank, esco_extract_rank, rrf_rank)
- evidence list đầy đủ (source_type, source_id, text, meta)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .enums import (
    RelationType,
    ConceptType,
    TierLevel,
    ConfidenceLevel,
    CourseType,
    DecisionStatus,
)


@dataclass(frozen=True)
class ExtractionInfo:
    """Thông tin về quá trình trích xuất đã sinh ra record này."""
    source: str                     # "escoxlmr_skill", "llm_fallback", ...
    matched_head_type: str | None   # "skill" / "knowledge" / None
    esco_type_agrees: bool | None   # True nếu head_type khớp ESCO skill_type


@dataclass(frozen=True)
class RetrievalInfo:
    """Thông tin ranking từ các kênh retrieval."""
    bm25_rank: int | None = None
    dense_rank: int | None = None
    esco_extract_skill_rank: int | None = None
    rrf_rank: int | None = None


@dataclass(frozen=True)
class EvidenceRef:
    """Tham chiếu tới 1 evidence unit đã contribute vào record."""
    source_type: str     # MO_TA, MUC_TIEU, CLO, BAI_HOC
    source_id: str       # G2, L1, L05, MAIN
    text: str            # Evidence text tiếng Anh
    meta: dict[str, Any] = field(default_factory=dict)
    # [PATCH v3.0 — Optional fields]
    evidence_weight: float = 0.30
    is_boilerplate: bool = False


@dataclass(frozen=True)
class SkillTeacherRecord:
    """Bản ghi output chính — ghi xuống JSON, nạp vào KG.

    Chứa đầy đủ thông tin provenance, extraction, retrieval
    để có thể giải thích tại sao course X được gán skill Y.
    """
    # Course info
    course_code: str
    course_title: str
    course_type: CourseType

    # Relation
    relation_type: RelationType
    concept_type: ConceptType

    # ESCO concept — LẤY TỪ ESCO, không phải text tự do
    esco_uri: str
    preferred_label: str
    skill_type: str           # "skill/competence" hoặc "knowledge" (từ ESCO)

    # Confidence
    confidence: float         # combined_score cuối cùng
    tier: TierLevel
    confidence_level: ConfidenceLevel
    decision_status: DecisionStatus = "ACCEPT"

    # Evidence provenance (danh sách đầy đủ)
    evidence: list[EvidenceRef] = field(default_factory=list)

    # Extraction info
    extraction: ExtractionInfo | None = None

    # Retrieval info
    retrieval: RetrievalInfo | None = None

    # Cross-encoder score riêng
    cross_encoder_score: float | None = None

    # Flags
    over_soft_cap: bool = False
    mismatch_flagged: bool = False   # Tầng 7 phát hiện mismatch
    # [PATCH v3.0 — Optional fields]
    mismatch_penalty_applied: bool = False
    retrieval_agreement: str = "PARTIAL"
    low_evidence_quality: bool = False

    # Metadata
    schema_version: str = "3.0"
    method: str = ""                 # Ví dụ: "ESCOXLM-R+esco-extract-skill+UniSkill"

    def to_dict(self) -> dict[str, Any]:
        """Serialize thành dict cho JSON export."""
        result: dict[str, Any] = {
            "course_code": self.course_code,
            "course_title": self.course_title,
            "course_type": self.course_type,
            "relation_type": self.relation_type,
            "concept_type": self.concept_type,
            "esco_uri": self.esco_uri,
            "preferred_label": self.preferred_label,
            "skill_type": self.skill_type,
            "confidence": self.confidence,
            "tier": self.tier,
            "confidence_level": self.confidence_level,
            "decision_status": self.decision_status,
            "evidence": [
                {
                    "source_type": e.source_type,
                    "source_id": e.source_id,
                    "text": e.text,
                    "meta": e.meta,
                    "evidence_weight": getattr(e, "evidence_weight", 0.30),
                    "is_boilerplate": getattr(e, "is_boilerplate", False),
                }
                for e in self.evidence
            ],
            "extraction": {
                "source": self.extraction.source,
                "matched_head_type": self.extraction.matched_head_type,
                "esco_type_agrees": self.extraction.esco_type_agrees,
            } if self.extraction else None,
            "retrieval": {
                "bm25_rank": self.retrieval.bm25_rank,
                "dense_rank": self.retrieval.dense_rank,
                "esco_extract_skill_rank": self.retrieval.esco_extract_skill_rank,
                "rrf_rank": self.retrieval.rrf_rank,
            } if self.retrieval else None,
            "model": {
                "cross_encoder_score": self.cross_encoder_score,
            },
            "over_soft_cap": self.over_soft_cap,
            "mismatch_flagged": self.mismatch_flagged,
            "mismatch_penalty_applied": self.mismatch_penalty_applied,
            "retrieval_agreement": self.retrieval_agreement,
            "low_evidence_quality": self.low_evidence_quality,
            "method": self.method,
            "schema_version": self.schema_version,
        }
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize thành JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
