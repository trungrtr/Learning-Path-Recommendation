"""Pydantic contracts for retrieval, validation, and course-skill output.

Only ``SkillCandidate`` and ``CourseSkillResult`` are external stage contracts.
The remaining models lock internal boundaries so later phases cannot bypass
pre-validation consolidation or lose evidence provenance.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _strip_required_text(value: Any) -> Any:
    return value.strip() if isinstance(value, str) else value


def _strip_optional_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned or None


NonEmptyText = Annotated[str, BeforeValidator(_strip_required_text), Field(min_length=1)]
OptionalText = Annotated[str | None, BeforeValidator(_strip_optional_text)]
UnitType = Literal["name", "description", "clo", "chapter", "lesson"]
QueryType = Literal[
    "course",
    "clo",
    "chapter",
    "lesson",
    # Legacy values remain readable until P4 migrates query generation.
    "direct",
    "course_ability",
    "clo_ability",
    "topic_ability",
]
RelationType = Literal["teaches", "supports"]
ValidationDecision = Literal["yes", "no", "insufficient"]


class _SkillContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContextualQuery(_SkillContract):
    """Internal query contract separating retrieval context from evidence."""

    course_id: NonEmptyText
    query_id: NonEmptyText
    query_type: QueryType
    retrieval_text_en: NonEmptyText
    evidence_text_en: NonEmptyText
    source_unit_ids: list[NonEmptyText] = Field(min_length=1)
    source_unit_types: list[UnitType] = Field(min_length=1)
    chunk_index: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_source_provenance(self) -> "ContextualQuery":
        if len(self.source_unit_ids) != len(self.source_unit_types):
            raise ValueError("source_unit_ids and source_unit_types must have equal length.")
        return self


class SkillCandidate(ContextualQuery):
    """External output contract for one Bi-Encoder query-skill candidate."""

    skill_id: NonEmptyText
    skill_uri: NonEmptyText
    skill_label: NonEmptyText
    skill_description: OptionalText = None
    retrieval_rank: int = Field(ge=1)
    retrieval_score: float = Field(ge=-1.0, le=1.0)


class RerankedCandidate(SkillCandidate):
    """Internal candidate after UniSkill_BERT scoring."""

    rerank_score: float = Field(ge=0.0, le=1.0)


class CandidateEvidence(_SkillContract):
    """One deduplicated source unit proposed as evidence for a skill."""

    unit_id: NonEmptyText
    unit_type: UnitType
    query_id: NonEmptyText
    evidence_text_en: NonEmptyText
    retrieval_score: float = Field(ge=-1.0, le=1.0)
    rerank_score: float = Field(ge=0.0, le=1.0)


class ConsolidatedCandidate(_SkillContract):
    """Exactly one validator request candidate per course and ESCO URI."""

    course_id: NonEmptyText
    skill_id: NonEmptyText
    skill_uri: NonEmptyText
    skill_label: NonEmptyText
    skill_description: OptionalText = None
    top_evidence: list[CandidateEvidence] = Field(min_length=1)
    best_retrieval_score: float = Field(ge=-1.0, le=1.0)
    best_rerank_score: float = Field(ge=0.0, le=1.0)


class EvidenceValidationResult(_SkillContract):
    """Structured output contract for the evidence validator."""

    course_id: NonEmptyText
    skill_uri: NonEmptyText
    decision: ValidationDecision
    relation_type: RelationType | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_unit_ids: list[NonEmptyText] = Field(default_factory=list)
    evidence_quotes: list[NonEmptyText] = Field(default_factory=list)
    reason: NonEmptyText

    @model_validator(mode="after")
    def validate_decision_evidence(self) -> "EvidenceValidationResult":
        if len(self.evidence_unit_ids) != len(self.evidence_quotes):
            raise ValueError("evidence_unit_ids and evidence_quotes must have equal length.")
        if self.decision == "yes":
            if self.relation_type is None:
                raise ValueError("An accepted skill requires relation_type.")
            if not self.evidence_unit_ids:
                raise ValueError("An accepted skill requires at least one evidence unit.")
        elif self.relation_type is not None:
            raise ValueError("Rejected or insufficient candidates must not have relation_type.")
        return self


class ValidatedCandidate(_SkillContract):
    """A consolidated ESCO candidate paired with its validator decision."""

    candidate: ConsolidatedCandidate
    validation: EvidenceValidationResult

    @model_validator(mode="after")
    def validate_identity(self) -> "ValidatedCandidate":
        if self.candidate.course_id != self.validation.course_id:
            raise ValueError("Candidate and validation course_id must match.")
        if self.candidate.skill_uri != self.validation.skill_uri:
            raise ValueError("Candidate and validation skill_uri must match.")
        return self


class CourseSkillEvidence(_SkillContract):
    unit_id: NonEmptyText
    unit_type: UnitType
    quote: NonEmptyText


class MatchedSkill(_SkillContract):
    skill_id: NonEmptyText
    skill_uri: NonEmptyText
    skill_label: NonEmptyText
    skill_description: OptionalText = None
    relation_type: RelationType
    retrieval_score: float = Field(ge=-1.0, le=1.0)
    rerank_score: float = Field(ge=0.0, le=1.0)
    validation_confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[CourseSkillEvidence] = Field(min_length=1)


class CourseSkillResult(_SkillContract):
    """External contract for one validated course-skill JSON file."""

    schema_version: Literal["1.0"] = "1.0"
    stage: Literal["course_skill_output"] = "course_skill_output"
    calibration_status: Literal["experimental", "calibrated"] = "experimental"
    limitations: list[NonEmptyText] = Field(default_factory=list)
    course_id: NonEmptyText
    course_code: OptionalText = None
    internal_course_code: OptionalText = None
    matched_skills: list[MatchedSkill] = Field(default_factory=list)
