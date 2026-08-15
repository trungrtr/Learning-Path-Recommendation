"""Merge Layer 1 source documents into strict Layer 2 canonical records."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings
from pipeline.extract_course.mo_hinh import ExtractedDocument

from .cleaning import clean_extracted_document, normalize_text, normalize_title
from .models import CanonicalDocument

LOGGER = logging.getLogger(__name__)


def _slug(value: str | None) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", (value or "").strip()).upper().strip("_") or "UNKNOWN"


def _normalized_value(value: Any) -> Any:
    return normalize_text(value) if isinstance(value, str) else value


def _pick_field(values: list[Any]) -> Any:
    """Pick the most frequent value, then the richest value on a tie."""
    candidates = [value for value in values if value is not None and value != ""]
    if not candidates:
        return None
    counts = Counter(_normalized_value(value) for value in candidates)
    return max(
        enumerate(candidates),
        key=lambda pair: (
            counts[_normalized_value(pair[1])],
            len(pair[1].strip()) if isinstance(pair[1], str) else 1,
            -pair[0],
        ),
    )[1]


def _merge_credits(courses: list[dict[str, Any]]) -> dict[str, Any]:
    credits = [course.get("credits", {}) for course in courses]
    return {
        field: _pick_field([value.get(field) for value in credits if isinstance(value, dict)])
        for field in ("total", "theory", "practice", "self_study")
    }


def _merge_description(values: list[str | None]) -> str | None:
    """Keep all distinct description evidence in one canonical text field."""
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        key = normalize_text(value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(value.strip())
    if not unique:
        return None
    richest = max(unique, key=len)
    if all(normalize_text(value) in normalize_text(richest) for value in unique):
        return richest
    return "\n\n".join(unique)


def _group_records(
    records: list[dict[str, Any]],
    key_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(key_fn(record), []).append(record)
    return list(grouped.values())


def _record_order(group: list[dict[str, Any]]) -> tuple[int, int]:
    order_values = [item.get("order_index") for item in group if isinstance(item.get("order_index"), int)]
    source_positions = [item["_source_position"] for item in group]
    return min(order_values, default=10**9), min(source_positions)


def _clo_group_key(record: dict[str, Any]) -> tuple[Any, ...]:
    code = normalize_text(record.get("clo_code"))
    return ("code", code) if code else ("content", normalize_text(record.get("content")))


def _chapter_group_key(record: dict[str, Any]) -> tuple[Any, ...]:
    code = normalize_text(record.get("chapter_code"))
    return ("code", code) if code else ("title", normalize_title(record.get("title")))


def _source_label(document: ExtractedDocument, fallback: str) -> str:
    return document.source_document.source_document_id or fallback


def merge_group(file_paths: list[Path], reports_dir: Path | None = None) -> dict[str, Any]:
    """Create one schema-valid canonical union from Layer 1 files."""
    if not file_paths:
        raise ValueError("merge_group requires at least one Layer 1 file.")

    documents: list[ExtractedDocument] = []
    chapter_keys_by_temp_id: dict[str, tuple[Any, ...]] = {}
    for path in file_paths:
        raw = json.loads(path.read_text(encoding="utf-8"))
        parsed = ExtractedDocument.model_validate(raw)
        cleaned, report = clean_extracted_document(parsed, source_id=_source_label(parsed, path.stem))
        for chapter in cleaned.chapters:
            if chapter.chapter_temp_id:
                chapter_keys_by_temp_id[chapter.chapter_temp_id] = _chapter_group_key(chapter.model_dump())
        documents.append(cleaned)
        if reports_dir is not None:
            reports_dir.mkdir(parents=True, exist_ok=True)
            report_path = reports_dir / f"cleaning_report_{path.stem}.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    source_keys = list(
        dict.fromkeys(
            document.source_document.crawl_course_key
            for document in documents
            if document.source_document.crawl_course_key
        )
    )
    if len(source_keys) > 1:
        raise ValueError(f"Cannot merge different crawl_course_key values: {source_keys}")

    course_dicts = [document.course.model_dump() for document in documents]
    course_code = _pick_field([course.get("course_code") for course in course_dicts])
    extracted_internal_code = _pick_field(
        [course.get("internal_course_code") for course in course_dicts]
    )
    internal_course_code = source_keys[0] if source_keys else extracted_internal_code
    base_id = internal_course_code or course_code or file_paths[0].stem
    digest = hashlib.sha1(base_id.encode("utf-8")).hexdigest()[:8]
    course_id = f"COURSE_{_slug(base_id)}_{digest}"

    clo_records: list[dict[str, Any]] = []
    chapter_records: list[dict[str, Any]] = []
    lesson_records: list[dict[str, Any]] = []
    position = 0
    for document in documents:
        for collection, destination in (
            (document.clos, clo_records),
            (document.chapters, chapter_records),
            (document.lessons, lesson_records),
        ):
            for item in collection:
                record = item.model_dump()
                record["_source_position"] = position
                destination.append(record)
                position += 1

    clo_groups = sorted(_group_records(clo_records, _clo_group_key), key=_record_order)
    clos = [
        {
            "clo_id": f"{course_id}_CLO{index}",
            "clo_code": _pick_field([item.get("clo_code") for item in group]),
            "content": _pick_field([item.get("content") for item in group]),
            "order_index": _pick_field([item.get("order_index") for item in group]),
        }
        for index, group in enumerate(clo_groups, start=1)
    ]

    chapter_groups = sorted(
        _group_records(chapter_records, _chapter_group_key),
        key=_record_order,
    )
    chapters: list[dict[str, Any]] = []
    canonical_chapter_by_group: dict[tuple[Any, ...], str] = {}
    for index, group in enumerate(chapter_groups, start=1):
        chapter_id = f"{course_id}_CH{index}"
        group_key = _chapter_group_key(group[0])
        canonical_chapter_by_group[group_key] = chapter_id
        chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_code": _pick_field([item.get("chapter_code") for item in group]),
                "title": _pick_field([item.get("title") for item in group]),
                "content_text": _pick_field([item.get("content_text") for item in group]),
                "order_index": _pick_field([item.get("order_index") for item in group]),
            }
        )

    canonical_chapter_by_temp_id = {
        temp_id: canonical_chapter_by_group[group_key]
        for temp_id, group_key in chapter_keys_by_temp_id.items()
        if group_key in canonical_chapter_by_group
    }
    for lesson in lesson_records:
        lesson["chapter_ref_id"] = canonical_chapter_by_temp_id.get(
            lesson.get("chapter_ref_temp_id")
        )

    lesson_groups = sorted(
        _group_records(
            lesson_records,
            lambda item: (
                item.get("chapter_ref_id"),
                normalize_title(item.get("title")),
            ),
        ),
        key=_record_order,
    )
    lessons = [
        {
            "lesson_id": f"{course_id}_L{index}",
            "chapter_ref_id": _pick_field([item.get("chapter_ref_id") for item in group]),
            "title": _pick_field([item.get("title") for item in group]),
            "order_index": _pick_field([item.get("order_index") for item in group]),
        }
        for index, group in enumerate(lesson_groups, start=1)
    ]

    result = {
        "schema_version": "2.3",
        "stage": "layer_2_canonical_course",
        "course": {
            "course_id": course_id,
            "course_code": course_code,
            "internal_course_code": internal_course_code,
            "name_vi": _pick_field([course.get("name_vi") for course in course_dicts]),
            "name_en": _pick_field([course.get("name_en") for course in course_dicts]),
            "credits": _merge_credits(course_dicts),
            "department": _pick_field([course.get("department") for course in course_dicts]),
            "knowledge_block": _pick_field(
                [course.get("knowledge_block") for course in course_dicts]
            ),
            "education_level": _pick_field(
                [course.get("education_level") for course in course_dicts]
            ),
        },
        "description": {
            "description_id": f"{course_id}_DESC",
            "text": _merge_description(
                [document.description.text for document in documents]
            ),
        },
        "clos": clos,
        "chapters": chapters,
        "lessons": lessons,
    }
    return CanonicalDocument.model_validate(result).model_dump()


def validate_canonical_course(course: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate the exact Layer 2 contract and lesson-to-chapter references."""
    try:
        document = CanonicalDocument.model_validate(course)
    except Exception as exc:
        return [{"type": "schema", "detail": str(exc)}]
    chapter_ids = {chapter.chapter_id for chapter in document.chapters}
    broken = [
        {
            "type": "broken_reference",
            "severity": "error",
            "field": "lessons.chapter_ref_id",
            "lesson_id": lesson.lesson_id,
        }
        for lesson in document.lessons
        if lesson.chapter_ref_id is not None and lesson.chapter_ref_id not in chapter_ids
    ]
    orphaned = [
        {
            "type": "orphan_lesson",
            "severity": "warning",
            "field": "lessons.chapter_ref_id",
            "lesson_id": lesson.lesson_id,
        }
        for lesson in document.lessons
        if lesson.chapter_ref_id is None
    ]
    return broken + orphaned


def _legacy_group_key(file_path: Path) -> str:
    return file_path.name.split("_")[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge Layer 1 files into Layer 2 canonical JSON.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reports", type=Path)
    parser.add_argument(
        "--group-by",
        choices=["course_key", "internal_course_code", "course_code"],
        default="course_key",
    )
    args = parser.parse_args()
    paths = load_settings(args.config)["paths"]
    input_dir = args.input or ROOT_DIR / paths["extracted_dir"]
    output_dir = args.output or ROOT_DIR / paths["canonical_dir"]
    reports_dir = args.reports or output_dir / "cleaning_reports"
    output_dir.mkdir(parents=True, exist_ok=True)

    groups: dict[str, list[Path]] = {}
    for file_path in sorted(input_dir.glob("*.json")):
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Skip invalid JSON %s: %s", file_path, exc)
            continue
        if data.get("stage") != "layer_1_source_extraction":
            continue
        if args.group_by == "course_key":
            group_key = (
                data.get("source_document", {}).get("crawl_course_key")
                or _legacy_group_key(file_path)
            )
        else:
            group_key = data.get("course", {}).get(args.group_by) or file_path.stem
        groups.setdefault(str(group_key), []).append(file_path)

    for group_key, source_files in groups.items():
        merged = merge_group(source_files, reports_dir=reports_dir)
        issues = validate_canonical_course(merged)
        errors = [issue for issue in issues if issue.get("severity") != "warning"]
        if errors:
            raise ValueError(f"Canonical validation failed for {group_key}: {errors}")
        for warning in issues:
            if warning.get("severity") == "warning":
                LOGGER.warning("Canonical warning for %s: %s", group_key, warning)
        output_path = output_dir / f"{merged['course']['course_id']}.json"
        output_path.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        LOGGER.info("Merged %d source files into %s", len(source_files), output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
