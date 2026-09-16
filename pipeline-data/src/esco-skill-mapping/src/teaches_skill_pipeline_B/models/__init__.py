"""Data models dùng chung cho teaches-skill pipeline v3.

Import tắt: ``from teaches_skill_pipeline.models import EvidenceUnit, RawMention, ...``
"""

from .enums import (
    SourceType,
    ConceptType,
    LoaiMucTieu,
    ContentRichness,
    ExtractionSource,
    HeadType,
    RetrievalChannel,
    TierLevel,
    ConfidenceLevel,
    RelationType,
    CourseType,
    DecisionStatus,
)
from .evidence import EvidenceUnit
from .mention import RawMention, DirectCandidate
from .candidate import RetrievalCandidate, FusedCandidate
from .record import (
    SkillTeacherRecord,
    ExtractionInfo,
    RetrievalInfo,
    EvidenceRef,
)

__all__ = [
    # Enums
    "SourceType",
    "ConceptType",
    "LoaiMucTieu",
    "ContentRichness",
    "ExtractionSource",
    "HeadType",
    "RetrievalChannel",
    "TierLevel",
    "ConfidenceLevel",
    "RelationType",
    "CourseType",
    "DecisionStatus",
    # Evidence
    "EvidenceUnit",
    # Mention
    "RawMention",
    "DirectCandidate",
    # Candidate
    "RetrievalCandidate",
    "FusedCandidate",
    # Record
    "SkillTeacherRecord",
    "ExtractionInfo",
    "RetrievalInfo",
    "EvidenceRef",
]
