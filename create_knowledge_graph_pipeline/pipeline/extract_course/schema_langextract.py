"""LangExtract schema for the semantic fields of the Layer 1 contract."""

from __future__ import annotations

from typing import Any


def _nullable(kind: str) -> dict[str, Any]:
    return {"anyOf": [{"type": kind}, {"type": "null"}]}


def build_output_schema(lx: Any) -> dict[str, Any]:
    """Build the grounded LLM schema.

    Temporary IDs, source provenance and lesson-to-chapter IDs are deliberately
    absent: :mod:`pipeline.extract_course.chuyen_doi` generates those deterministically.
    ``chapter_code`` on a lesson is only a mapping hint and is not serialized.
    """
    text = _nullable("string")
    number = _nullable("number")
    integer = _nullable("integer")
    return lx.schema.extractions_schema(
        lx.schema.extraction_item_schema(
            "course",
            attributes={
                "course_code": text,
                "name_vi": text,
                "name_en": text,
                "credits_total": number,
                "credits_theory": number,
                "credits_practice": number,
                "credits_self_study": number,
                "department": text,
                "knowledge_block": text,
                "education_level": text,
                "description_text": text,
            },
        ),
        lx.schema.extraction_item_schema(
            "clo",
            attributes={"clo_code": text, "content": text, "order_index": integer},
        ),
        lx.schema.extraction_item_schema(
            "chapter",
            attributes={
                "chapter_code": text,
                "title": text,
                "content_text": text,
                "order_index": integer,
            },
        ),
        lx.schema.extraction_item_schema(
            "lesson",
            attributes={"chapter_code": text, "title": text, "order_index": integer},
        ),
    )
