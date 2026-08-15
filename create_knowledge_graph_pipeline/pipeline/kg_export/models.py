"""Pydantic contract for the Neo4j-ready KG export boundary.

P0 defines only the data contract.  CSV serialization and orchestration remain
deferred to P11 so this package does not become a partially implemented stage.
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


class _KGContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CourseNode(_KGContract):
    course_id: NonEmptyText
    course_code: OptionalText = None
    internal_course_code: OptionalText = None
    name_vi: OptionalText = None
    name_en: OptionalText = None


class DescriptionNode(_KGContract):
    description_id: NonEmptyText
    text_vi: OptionalText = None
    text_en: OptionalText = None


class CloNode(_KGContract):
    clo_id: NonEmptyText
    clo_code: OptionalText = None
    content_vi: OptionalText = None
    content_en: OptionalText = None


class ChapterNode(_KGContract):
    chapter_id: NonEmptyText
    chapter_code: OptionalText = None
    title_vi: OptionalText = None
    title_en: OptionalText = None


class LessonNode(_KGContract):
    lesson_id: NonEmptyText
    course_code: OptionalText = None
    internal_course_code: OptionalText = None
    title_vi: OptionalText = None
    title_en: OptionalText = None


class EscoSkillNode(_KGContract):
    skill_uri: NonEmptyText
    skill_id: NonEmptyText
    skill_label: NonEmptyText
    skill_description: OptionalText = None


class OccupationNode(_KGContract):
    occupation_uri: NonEmptyText
    occupation_id: NonEmptyText
    occupation_label: NonEmptyText
    occupation_description: OptionalText = None


class OccupationSkillRelationship(_KGContract):
    occupation_uri: NonEmptyText
    skill_uri: NonEmptyText
    relation_type: Literal["essential", "optional"]
    kg_relationship: Literal["REQUIRES_SKILL", "OPTIONAL_SKILL"]


class EntityRelationship(_KGContract):
    source_id: NonEmptyText
    target_id: NonEmptyText
    relationship_type: Literal[
        "HAS_DESCRIPTION",
        "HAS_CLO",
        "HAS_CHAPTER",
        "HAS_LESSON",
    ]


class CourseSkillRelationship(_KGContract):
    course_id: NonEmptyText
    skill_uri: NonEmptyText
    relationship_type: Literal["TEACHES_SKILL", "SUPPORTS_SKILL"]
    retrieval_score: float = Field(ge=-1.0, le=1.0)
    rerank_score: float = Field(ge=0.0, le=1.0)
    validation_confidence: float = Field(ge=0.0, le=1.0)
    evidence_unit_ids: list[NonEmptyText] = Field(min_length=1)
    evidence_quotes: list[NonEmptyText] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_evidence_alignment(self) -> "CourseSkillRelationship":
        if len(self.evidence_unit_ids) != len(self.evidence_quotes):
            raise ValueError("evidence_unit_ids and evidence_quotes must have equal length.")
        return self


class KGExport(_KGContract):
    """In-memory contract from which deterministic Neo4j CSVs are exported."""

    schema_version: Literal["1.0"] = "1.0"
    stage: Literal["kg_export"] = "kg_export"
    courses: list[CourseNode] = Field(default_factory=list)
    descriptions: list[DescriptionNode] = Field(default_factory=list)
    clos: list[CloNode] = Field(default_factory=list)
    chapters: list[ChapterNode] = Field(default_factory=list)
    lessons: list[LessonNode] = Field(default_factory=list)
    esco_skills: list[EscoSkillNode] = Field(default_factory=list)
    occupations: list[OccupationNode] = Field(default_factory=list)
    entity_relationships: list[EntityRelationship] = Field(default_factory=list)
    course_skill_relationships: list[CourseSkillRelationship] = Field(default_factory=list)
    occupation_skill_relationships: list[OccupationSkillRelationship] = Field(default_factory=list)


class CtdtProgramNode(_KGContract):
    program_id: NonEmptyText
    ma_ctdt: OptionalText = None
    ten_nganh: OptionalText = None


class CtdtGroupNode(_KGContract):
    group_id: NonEmptyText
    program_id: NonEmptyText
    nhom_id: OptionalText = None
    ten_nhom: OptionalText = None
    nhom_cha_id: OptionalText = None
    tong_so_tin: float | None = None


class CtdtProgramGroupRelationship(_KGContract):
    program_id: NonEmptyText
    group_id: NonEmptyText
    relationship_type: Literal["HAS_GROUP"] = "HAS_GROUP"


class CtdtGroupRelationship(_KGContract):
    parent_group_id: NonEmptyText
    child_group_id: NonEmptyText
    relationship_type: Literal["HAS_SUBGROUP"] = "HAS_SUBGROUP"


class CtdtCourseRelationship(_KGContract):
    program_id: NonEmptyText
    group_id: NonEmptyText
    ma_hp: NonEmptyText
    hoc_ky: int | None = None
    relationship_type: Literal["INCLUDES_COURSE"] = "INCLUDES_COURSE"


class CtdtCourseDependencyRelationship(_KGContract):
    ma_hp: NonEmptyText
    dependency_ma_hp: NonEmptyText
    dependency_type: Literal["TIEN_QUYET", "HOC_TRUOC"]
    relationship_type: Literal["REQUIRES_COURSE", "RECOMMENDS_PRIOR_COURSE"]


class CtdtKGExport(_KGContract):
    """Programme-level graph export built from ``extract_ctdt`` output."""

    schema_version: Literal["1.0"] = "1.0"
    stage: Literal["ctdt_kg_export"] = "ctdt_kg_export"
    programs: list[CtdtProgramNode] = Field(default_factory=list)
    groups: list[CtdtGroupNode] = Field(default_factory=list)
    program_group_relationships: list[CtdtProgramGroupRelationship] = Field(default_factory=list)
    group_relationships: list[CtdtGroupRelationship] = Field(default_factory=list)
    course_relationships: list[CtdtCourseRelationship] = Field(default_factory=list)
    course_dependency_relationships: list[CtdtCourseDependencyRelationship] = Field(default_factory=list)
