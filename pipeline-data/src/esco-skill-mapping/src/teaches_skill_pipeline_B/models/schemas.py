"""Data contracts cho teaches-skill pipeline v3 (layers-based architecture).

Gộp tất cả enums, schemas, và models vào chung 1 file để tiện quản lý.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# 1. Enums
# ---------------------------------------------------------------------------
SourceType = Literal["MO_TA", "MUC_TIEU", "CLO", "BAI_HOC"]
ConceptType = Literal["skill", "knowledge"]
LoaiMucTieu = Literal["KIEN_THUC", "KY_NANG", "TU_CHU_TRACH_NHIEM"]
ContentRichness = Literal["full", "title_only"]
ExtractionSource = Literal[
    "escoxlmr_skill",
    "escoxlmr_knowledge",
    "esco_extract_skill",
    "skillspan",
    "llm_fallback",
]
HeadType = Literal["skill", "knowledge"]
RetrievalChannel = Literal["bm25", "dense", "esco_extract"]
TierLevel = Literal["PRIMARY", "SECONDARY", "OPTIONAL", "HIGH", "MED", "low_confidence"]
ConfidenceLevel = Literal["HIGH", "MED", "LOW"]
RelationType = Literal["TEACHES_SKILL", "TEACHES_KNOWLEDGE"]
CourseType = Literal["FOUNDATIONAL", "CORE", "SPECIALIZED"]
DecisionStatus = Literal["ACCEPT", "REVIEW", "REJECT"]

# ---------------------------------------------------------------------------
# 2. Pydantic Schemas (Input Data)
# ---------------------------------------------------------------------------
class CtdtMembership(BaseModel):
    ma_ctdt: str = ""
    nhom_id: str | None = None
    loai_nhom: str | None = None

class HocPhanSchema(BaseModel):
    ma_hoc_phan: str
    ten_vi: str | None = None
    ten_en: str | None = None
    mo_ta_tom_tat: str | None = None
    mo_ta_tom_tat_en: str | None = None
    so_tin_chi_tong: int | None = None
    ctdt_memberships: list[CtdtMembership] = Field(default_factory=list)
    source_hash: str | None = None

class CloSchema(BaseModel):
    ma_cdr_goc: str | None = None
    ma_clo: str | None = None
    noi_dung: str | None = None
    noi_dung_en: str | None = None
    pi_so: list[str] = Field(default_factory=list)
    muc_do: str | None = None
    source_hash: str | None = None

class BaiHocSchema(BaseModel):
    ten_bai: str | None = None
    ten_bai_en: str | None = None
    noi_dung_tom_tat: str | None = None
    noi_dung_tom_tat_en: str | None = None
    ma_clo: list[str] = Field(default_factory=list)
    source_hash: str | None = None

class MucTieuSchema(BaseModel):
    ma_muc_tieu: str | None = None
    loai_muc_tieu: str | None = None
    noi_dung: str | None = None
    noi_dung_en: str | None = None
    so_ctdt: list[str] = Field(default_factory=list)
    source_hash: str | None = None

class CourseData(BaseModel):
    ma_hoc_phan: str
    hoc_phan: HocPhanSchema
    clo: list[CloSchema] = Field(default_factory=list)
    bai_hoc: list[BaiHocSchema] = Field(default_factory=list)
    muc_tieu: list[MucTieuSchema] = Field(default_factory=list)
    source_hashes: dict[str, str] = Field(default_factory=dict)

# ---------------------------------------------------------------------------
# 3. Pipeline Data Classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceUnit:
    evidence_id: str
    course_code: str
    source_type: SourceType
    source_id: str
    text: str
    text_vi: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    evidence_weight: float = 0.30
    is_boilerplate: bool = False

    @property
    def content_richness(self) -> ContentRichness:
        return self.meta.get("content_richness", "full")

    @property
    def loai_muc_tieu(self) -> LoaiMucTieu | None:
        return self.meta.get("loai_muc_tieu")

    @property
    def linked_clo(self) -> list[str]:
        return self.meta.get("linked_clo", [])

@dataclass(frozen=True)
class RawMention:
    text: str
    evidence_id: str
    source: ExtractionSource
    head_type: HeadType | None = None
    confidence: float | None = None
    char_start: int | None = None
    char_end: int | None = None
    source_text: str = ""

@dataclass(frozen=True)
class DirectCandidate:
    skill_uri: str
    skill_label: str
    evidence_id: str
    score: float = 0.0
    source: ExtractionSource = "esco_extract_skill"

@dataclass
class RetrievalCandidate:
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
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]

@dataclass
class FusedCandidate:
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
    evidence_mentions: dict[str, list[str]] = field(default_factory=dict)
    extraction_sources: list[ExtractionSource] = field(default_factory=list)
    head_types: list[HeadType | None] = field(default_factory=list)
    bm25_rank: int | None = None
    dense_rank: int | None = None
    esco_extract_rank: int | None = None
    retrieval_agreement: str = "PARTIAL"
    low_evidence_quality: bool = False

    @property
    def skill_id(self) -> str:
        return self.skill_uri.rstrip("/").rsplit("/", 1)[-1]

@dataclass(frozen=True)
class ExtractionInfo:
    source: str
    matched_head_type: str | None
    esco_type_agrees: bool | None

@dataclass(frozen=True)
class RetrievalInfo:
    bm25_rank: int | None = None
    dense_rank: int | None = None
    esco_extract_skill_rank: int | None = None
    rrf_rank: int | None = None

@dataclass(frozen=True)
class EvidenceRef:
    source_type: str
    source_id: str
    text: str
    meta: dict[str, Any] = field(default_factory=dict)
    evidence_weight: float = 0.30
    is_boilerplate: bool = False

@dataclass(frozen=True)
class SkillTeacherRecord:
    course_code: str
    course_title: str
    course_type: CourseType
    relation_type: RelationType
    concept_type: ConceptType
    esco_uri: str
    preferred_label: str
    skill_type: str
    confidence: float
    tier: TierLevel
    confidence_level: ConfidenceLevel
    decision_status: DecisionStatus = "ACCEPT"
    evidence: list[EvidenceRef] = field(default_factory=list)
    extraction: ExtractionInfo | None = None
    retrieval: RetrievalInfo | None = None
    cross_encoder_score: float | None = None
    reject_reason: str | None = None
    over_soft_cap: bool = False
    mismatch_flagged: bool = False
    mismatch_penalty_applied: bool = False
    retrieval_agreement: str = "PARTIAL"
    low_evidence_quality: bool = False
    schema_version: str = "3.0"
    method: str = ""
    llm_reasoning: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
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
            "llm_reasoning": self.llm_reasoning,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
