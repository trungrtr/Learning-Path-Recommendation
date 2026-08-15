"""Strict Pydantic contract for ``layer2_canonical_course_schema.json``."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

def _clean_optional_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned or None


OptionalText = Annotated[str | None, BeforeValidator(_clean_optional_text)]


class _CanonicalModel(BaseModel):
    # Layer 2 is the canonical boundary: undeclared fields are programming
    # errors and must never leak into downstream JSON.
    model_config = ConfigDict(extra="forbid")


class CanonicalCredits(_CanonicalModel):
    total: float | None = None
    theory: float | None = None
    practice: float | None = None
    self_study: float | None = None


class CanonicalCourse(_CanonicalModel):
    course_id: str
    course_code: OptionalText = None
    internal_course_code: OptionalText = None
    name_vi: OptionalText = None
    name_en: OptionalText = None
    credits: CanonicalCredits = Field(default_factory=CanonicalCredits)
    department: OptionalText = None
    knowledge_block: OptionalText = None
    education_level: OptionalText = None


class CanonicalDescription(_CanonicalModel):
    description_id: str
    text: OptionalText = None


class CanonicalClo(_CanonicalModel):
    clo_id: str
    clo_code: OptionalText = None
    content: OptionalText = None
    order_index: int | None = None


class CanonicalChapter(_CanonicalModel):
    chapter_id: str
    chapter_code: OptionalText = None
    title: OptionalText = None
    content_text: OptionalText = None
    order_index: int | None = None


class CanonicalLesson(_CanonicalModel):
    lesson_id: str
    chapter_ref_id: OptionalText = None
    title: OptionalText = None
    order_index: int | None = None


class CanonicalDocument(_CanonicalModel):
    schema_version: Literal["2.3"] = "2.3"
    stage: Literal["layer_2_canonical_course"] = "layer_2_canonical_course"
    course: CanonicalCourse
    description: CanonicalDescription
    clos: list[CanonicalClo] = Field(default_factory=list)
    chapters: list[CanonicalChapter] = Field(default_factory=list)
    lessons: list[CanonicalLesson] = Field(default_factory=list)
