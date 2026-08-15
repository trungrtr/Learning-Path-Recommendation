"""Conservative Layer 1 cleaning before canonical merge."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Callable, TypeVar

from rapidfuzz import fuzz

from pipeline.extract_course.mo_hinh import Chapter, Clo, ExtractedDocument, Lesson
from pipeline.extract_course.noise_rules import apply_lightweight_noise_rules

T = TypeVar("T")
CODE_ONLY_PATTERN = re.compile(r"^(?:CLO|C)?\s*\d+(?:\.\d+)*$", re.IGNORECASE)
CONTINUATION_SUFFIX_PATTERN = re.compile(
    r"\s*(?:\(|\[)?(?:tiếp|tiếp theo|continued)(?:\)|\])?\s*$",
    re.IGNORECASE,
)
NON_ACADEMIC_SUFFIX_PATTERN = re.compile(
    r"\s*(?:/|-)?\s*(?:ôn\s*tập|kiểm\s*tra|bài\s*tập)\s*$",
    re.IGNORECASE,
)
PRACTICE_LESSON_PATTERN = re.compile(
    r"^(?:bài\s*(?:thực\s*hành|tập)|thực\s*hành|ôn\s*tập|kiểm\s*tra|thi)\b",
    re.IGNORECASE,
)

def normalize_text(value: str | None) -> str:
    """Return a stable comparison form without altering Vietnamese characters."""
    normalized = unicodedata.normalize("NFC", value or "")
    normalized = re.sub(r"\s+", " ", normalized).strip().casefold()
    return re.sub(r"([,.;:!?])\1+", r"\1", normalized)


def normalize_title(value: str | None) -> str:
    """Normalize a title and remove presentation-only continuation suffixes."""
    return CONTINUATION_SUFFIX_PATTERN.sub("", normalize_text(value)).strip()


def _clean_text(value: str | None) -> str | None:
    cleaned = unicodedata.normalize("NFC", value or "").strip()
    return cleaned or None


def _clean_title(value: str | None) -> str | None:
    """Clean a title and actually strip the continuation suffix, preserving case."""
    cleaned = _clean_text(value)
    if cleaned:
        cleaned = CONTINUATION_SUFFIX_PATTERN.sub("", cleaned).strip()
        cleaned = NON_ACADEMIC_SUFFIX_PATTERN.sub("", cleaned).strip()
    return cleaned or None


def is_garbage_clo(clo_content: str | None, clo_code: str | None) -> bool:
    """Detect content that merely repeats a CLO code."""
    if not clo_content or not clo_code:
        return False
    content = normalize_text(clo_content)
    code = normalize_text(clo_code)
    return content == code or bool(CODE_ONLY_PATTERN.fullmatch(clo_content.strip()))


def _richness(item: Any) -> int:
    """Score completeness, favoring records with richer textual evidence."""
    score = 0
    for value in item.model_dump().values():
        if isinstance(value, str) and value.strip():
            score += len(value.strip())
        elif value is not None:
            score += 1
    return score


def _deduplicate_exact(
    items: list[T],
    key_fn: Callable[[T], tuple[Any, ...]],
    record_type: str,
    report_items: list[dict[str, Any]],
) -> list[T]:
    """Drop only exact semantic duplicates and preserve first-seen ordering."""
    positions: dict[tuple[Any, ...], int] = {}
    result: list[T] = []
    for item in items:
        key = key_fn(item)
        if key not in positions:
            positions[key] = len(result)
            result.append(item)
            continue
        position = positions[key]
        if _richness(item) > _richness(result[position]):
            result[position] = item
        report_items.append(
            {
                "type": record_type,
                "reason": "exact_duplicate",
                "detail": {"deduplication_key": list(key)},
                "action": "dropped_keep_richer_equivalent",
            }
        )
    return result


def _clo_key(clo: Clo) -> tuple[Any, ...]:
    code = normalize_text(clo.clo_code)
    return ("code", code) if code else ("content", normalize_text(clo.content))


def _chapter_key(chapter: Chapter) -> tuple[Any, ...]:
    code = normalize_text(chapter.chapter_code)
    return ("code", code) if code else ("title", normalize_title(chapter.title))


def _lesson_key(lesson: Lesson) -> tuple[Any, ...]:
    return normalize_text(lesson.chapter_ref_temp_id), normalize_title(lesson.title)


def clean_extracted_document(
    doc: ExtractedDocument,
    source_id: str | None = None,
) -> tuple[ExtractedDocument, dict[str, Any]]:
    """Normalize whitespace and remove only garbage or exact duplicates.

    Near-duplicate lessons are retained and reported because they may represent
    separate teaching sessions with similar titles.
    """
    cleaned, noise_report = apply_lightweight_noise_rules(doc)
    source_id = source_id or cleaned.source_document.source_document_id or "unknown"
    report_items: list[dict[str, Any]] = [
        {
            "type": item.record_type,
            "reason": item.reason,
            "detail": {
                "record_id": item.record_id,
                "original_text": item.original_text,
            },
            "action": item.action,
        }
        for item in noise_report.items
    ]

    for field in (
        "course_code",
        "internal_course_code",
        "name_vi",
        "name_en",
        "department",
        "knowledge_block",
        "education_level",
    ):
        setattr(cleaned.course, field, _clean_text(getattr(cleaned.course, field)))
    cleaned.description.text = _clean_text(cleaned.description.text)
    for clo in cleaned.clos:
        clo.clo_code = _clean_text(clo.clo_code)
        clo.content = _clean_text(clo.content)
    for chapter in cleaned.chapters:
        chapter.chapter_code = _clean_text(chapter.chapter_code)
        chapter.title = _clean_title(chapter.title)
        chapter.content_text = _clean_text(chapter.content_text)
    for lesson in cleaned.lessons:
        lesson.chapter_ref_temp_id = _clean_text(lesson.chapter_ref_temp_id)
        lesson.title = _clean_title(lesson.title)

    retained_clos: list[Clo] = []
    for clo in cleaned.clos:
        if is_garbage_clo(clo.content, clo.clo_code):
            report_items.append(
                {
                    "type": "clo",
                    "reason": "garbage_clo",
                    "detail": {"clo_code": clo.clo_code, "content": clo.content},
                    "action": "dropped",
                }
            )
        elif clo.clo_code or clo.content:
            retained_clos.append(clo)
    cleaned.clos = _deduplicate_exact(retained_clos, _clo_key, "clo", report_items)
    cleaned.chapters = _deduplicate_exact(
        [item for item in cleaned.chapters if item.chapter_code or item.title or item.content_text],
        _chapter_key,
        "chapter",
        report_items,
    )
    retained_lessons: list[Lesson] = []
    for lesson in cleaned.lessons:
        if not lesson.title:
            continue
        if PRACTICE_LESSON_PATTERN.search(lesson.title):
            report_items.append(
                {
                    "type": "lesson",
                    "reason": "practice_or_exercise",
                    "detail": {"title": lesson.title},
                    "action": "dropped",
                }
            )
            continue
        retained_lessons.append(lesson)

    cleaned.lessons = _deduplicate_exact(
        retained_lessons,
        _lesson_key,
        "lesson",
        report_items,
    )

    for previous, current in zip(cleaned.lessons, cleaned.lessons[1:]):
        if previous.title and current.title:
            ratio = fuzz.ratio(normalize_text(previous.title), normalize_text(current.title))
            if ratio > 90 and _lesson_key(previous) != _lesson_key(current):
                report_items.append(
                    {
                        "type": "lesson",
                        "reason": "near_duplicate_candidate",
                        "detail": {
                            "previous_title": previous.title,
                            "current_title": current.title,
                            "similarity": ratio,
                        },
                        "action": "review_required_kept",
                    }
                )

    return cleaned, {"source_document_id": source_id, "items": report_items}
