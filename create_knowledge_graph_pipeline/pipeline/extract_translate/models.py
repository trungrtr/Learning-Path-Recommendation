"""Pydantic contracts for hierarchical source and translated course units.

These models lock the boundary between the canonical Layer 2 document and the
translation/query stages.  Runtime adoption is intentionally deferred to P3;
P0 only defines and tests the contract without changing existing APIs.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _strip_required_text(value: Any) -> Any:
    """Strip required strings so whitespace-only values fail ``min_length``."""
    return value.strip() if isinstance(value, str) else value


def _strip_optional_text(value: Any) -> Any:
    """Normalize optional blank strings to ``None``."""
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned or None


NonEmptyText = Annotated[str, BeforeValidator(_strip_required_text), Field(min_length=1)]
OptionalText = Annotated[str | None, BeforeValidator(_strip_optional_text)]
UnitType = Literal["name", "description", "clo", "chapter", "lesson"]


class _UnitContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceUnit(_UnitContract):
    """A canonical Vietnamese text unit before translation.

    ``unit_id`` always reuses an identifier from Layer 2.  Optional hierarchy
    fields remain nullable so an orphan lesson retained by Merge is still a
    valid, auditable unit.
    """

    course_id: NonEmptyText
    unit_id: NonEmptyText
    unit_type: UnitType
    course_code: OptionalText = None
    internal_course_code: OptionalText = None
    knowledge_block: OptionalText = None
    course_name_vi: OptionalText = None
    course_name_en: OptionalText = None
    description_id: OptionalText = None
    clo_id: OptionalText = None
    chapter_id: OptionalText = None
    lesson_id: OptionalText = None
    chapter_title_vi: OptionalText = None
    chapter_title_en: OptionalText = None
    text_vi: NonEmptyText
    text_src: NonEmptyText

    @model_validator(mode="after")
    def validate_canonical_unit_id(self) -> "SourceUnit":
        """Require the Layer 2 identifier corresponding to each unit type."""
        id_fields = {
            "description": "description_id",
            "clo": "clo_id",
            "chapter": "chapter_id",
            "lesson": "lesson_id",
        }
        if self.unit_type == "name":
            if self.unit_id != self.course_id:
                raise ValueError("A name unit must reuse course_id as unit_id.")
            return self

        id_field = id_fields[self.unit_type]
        canonical_id = getattr(self, id_field)
        if canonical_id is None:
            raise ValueError(f"A {self.unit_type} unit requires {id_field}.")
        if self.unit_id != canonical_id:
            raise ValueError(f"A {self.unit_type} unit must reuse {id_field} as unit_id.")
        return self


class TranslatedUnit(SourceUnit):
    """A hierarchy-preserving course unit with an approved English text."""

    text_en: NonEmptyText

