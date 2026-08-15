"""Map grounded LangExtract records to the complete Layer 1 contract."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from pipeline.extract_course.mo_hinh import (
    Chapter,
    Clo,
    Course,
    Credits,
    Description,
    ExtractedDocument,
    Lesson,
    SourceDocument,
)


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper() or "UNKNOWN"


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _append_distinct_text(current: str | None, candidate: Any) -> str | None:
    """Preserve distinct grounded description fragments in source order."""
    candidate_text = _text(candidate)
    if candidate_text is None:
        return current
    if current is None:
        return candidate_text
    normalized_parts = {part.casefold() for part in current.split("\n\n")}
    return current if candidate_text.casefold() in normalized_parts else f"{current}\n\n{candidate_text}"


def _first_defined(target: dict[str, Any], key: str, value: Any) -> None:
    if target.get(key) is None and value is not None:
        target[key] = value


def _merge_course_fields(
    course_values: dict[str, Any],
    credit_values: dict[str, Any],
    attributes: dict[str, Any],
) -> None:
    """Coalesce repeated course extractions without replacing grounded values."""
    for key in (
        "course_code",
        "name_vi",
        "name_en",
        "department",
        "knowledge_block",
        "education_level",
    ):
        _first_defined(course_values, key, _text(attributes.get(key)))
    for source_key, target_key in (
        ("credits_total", "total"),
        ("credits_theory", "theory"),
        ("credits_practice", "practice"),
        ("credits_self_study", "self_study"),
    ):
        _first_defined(credit_values, target_key, attributes.get(source_key))


def build_document(
    markdown_path: Path,
    extractions: list[Any],
    course_key: str,
    model_id: str,
) -> ExtractedDocument:
    """Create one lossless, schema-valid Layer 1 document.

    ``model_id`` remains in the public interface for compatibility.  It is not
    serialized because the v1.2 schema intentionally excludes runtime metadata.
    """
    del model_id
    source_hash = hashlib.sha256(markdown_path.read_bytes()).hexdigest()
    source_id = f"SD_{_slugify(markdown_path.stem)}_{source_hash[:12]}"
    course_values: dict[str, Any] = {}
    credit_values: dict[str, Any] = {}
    description_text: str | None = None
    raw_clos: list[dict[str, Any]] = []
    raw_chapters: list[dict[str, Any]] = []
    raw_lessons: list[dict[str, Any]] = []

    for item in extractions:
        attributes = dict(item.attributes or {})
        extraction_text = _text(item.extraction_text)
        if item.extraction_class == "course":
            _merge_course_fields(course_values, credit_values, attributes)
            description_text = _append_distinct_text(description_text, attributes.get("description_text"))
        elif item.extraction_class == "clo":
            content = _text(attributes.get("content")) or extraction_text
            clo_code = _text(attributes.get("clo_code"))
            if content or clo_code:
                raw_clos.append(
                    {
                        "clo_code": clo_code,
                        "content": content,
                        "order_index": attributes.get("order_index"),
                    }
                )
        elif item.extraction_class == "chapter":
            chapter_code = _text(attributes.get("chapter_code"))
            title = _text(attributes.get("title")) or extraction_text
            content_text = _text(attributes.get("content_text")) or extraction_text
            if chapter_code or title or content_text:
                raw_chapters.append(
                    {
                        "chapter_code": chapter_code,
                        "title": title,
                        "content_text": content_text,
                        "order_index": attributes.get("order_index"),
                    }
                )
        elif item.extraction_class == "lesson":
            title = _text(attributes.get("title")) or extraction_text
            if title:
                raw_lessons.append(
                    {
                        "chapter_code": _text(attributes.get("chapter_code")),
                        "title": title,
                        "order_index": attributes.get("order_index"),
                    }
                )

    chapters = [
        Chapter(chapter_temp_id=f"{source_id}_CH{index}", **raw)
        for index, raw in enumerate(raw_chapters, start=1)
    ]
    chapter_ids_by_code = {
        _slugify(chapter.chapter_code): chapter.chapter_temp_id
        for chapter in chapters
        if chapter.chapter_code and chapter.chapter_temp_id
    }
    lessons = [
        Lesson(
            lesson_temp_id=f"{source_id}_L{index}",
            chapter_ref_temp_id=chapter_ids_by_code.get(_slugify(raw["chapter_code"]))
            if raw["chapter_code"]
            else None,
            title=raw["title"],
            order_index=raw["order_index"],
        )
        for index, raw in enumerate(raw_lessons, start=1)
    ]

    # The stable upstream key is the authoritative internal course code.  The
    # LLM only extracts the separate catalogue course_code printed in the file.
    course_values["internal_course_code"] = _text(course_key)
    return ExtractedDocument(
        schema_version="1.2",
        source_document=SourceDocument(
            source_document_id=source_id,
            crawl_course_key=course_key,
        ),
        course=Course(
            course_temp_id=f"{source_id}_COURSE",
            credits=Credits(**credit_values),
            **course_values,
        ),
        description=Description(
            description_temp_id=f"{source_id}_DESC",
            text=description_text,
        ),
        clos=[
            Clo(clo_temp_id=f"{source_id}_CLO{index}", **raw)
            for index, raw in enumerate(raw_clos, start=1)
        ],
        chapters=chapters,
        lessons=lessons,
    )
