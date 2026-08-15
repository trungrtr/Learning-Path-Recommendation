"""Canonical course -> hierarchical text units -> approved English units."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, MutableMapping
from typing import Any

from pipeline.extract_translate.glossary import load_glossary, translate_with_glossary
from pipeline.extract_translate.models import SourceUnit, TranslatedUnit

Unit = dict[str, Any]
TranslateFunction = Callable[[list[str]], list[str]]
DEFAULT_PROMPT_VERSION = "academic_vi_en_v2"


def _non_empty_text(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _legacy_extract_units(course: dict[str, Any], course_id: str) -> list[Unit]:
    """Keep the old flat input API readable during migration.

    Production Layer 2 input follows the canonical branch below and never uses
    generated unit IDs. This branch is retained only for backward compatibility.
    """
    units: list[Unit] = []
    name_vi = _non_empty_text(course.get("name_vi"))
    name_en = _non_empty_text(course.get("name_en"))
    if name_vi or name_en:
        units.append(
            {
                "course_id": course_id,
                "unit_type": "name",
                "unit_id": "name_1",
                "text_vi": name_vi or name_en,
                "text_src": name_en or name_vi,
            }
        )
    for unit_type, values in (
        ("clo", course.get("clos")),
        ("chapter", course.get("chapters")),
        ("lesson", course.get("lessons")),
    ):
        if not isinstance(values, list):
            continue
        for index, value in enumerate(values, start=1):
            text = _non_empty_text(value)
            if text:
                units.append(
                    {
                        "course_id": course_id,
                        "unit_type": unit_type,
                        "unit_id": f"{unit_type}_{index}",
                        "text_vi": text,
                        "text_src": text,
                    }
                )
    return units


def _canonical_unit(common: dict[str, Any], **values: Any) -> Unit:
    """Validate one canonical source unit before it crosses the stage boundary."""
    return SourceUnit(**common, **values).model_dump(exclude_none=True)


def extract_units(course: dict[str, Any]) -> list[Unit]:
    """Extract hierarchy-preserving units from a Layer 2 canonical document.

    Canonical IDs are reused as unit IDs. A retained orphan lesson remains
    valid with ``chapter_id=None`` and therefore stays auditable downstream.
    Legacy flat input remains readable through a compatibility branch.
    """
    course_info = course.get("course")
    if not isinstance(course_info, dict):
        legacy_course_id = _non_empty_text(course.get("course_id"))
        return _legacy_extract_units(course, legacy_course_id) if legacy_course_id else []

    course_id = _non_empty_text(course_info.get("course_id"))
    if course_id is None:
        return []
    name_vi = _non_empty_text(course_info.get("name_vi"))
    name_en = _non_empty_text(course_info.get("name_en"))
    common = {
        "course_id": course_id,
        "course_code": _non_empty_text(course_info.get("course_code")),
        "internal_course_code": _non_empty_text(course_info.get("internal_course_code")),
        "knowledge_block": _non_empty_text(course_info.get("knowledge_block")),
        "course_name_vi": name_vi,
        "course_name_en": name_en,
    }
    units: list[Unit] = []
    if name_vi or name_en:
        units.append(
            _canonical_unit(
                common,
                unit_id=course_id,
                unit_type="name",
                text_vi=name_vi or name_en,
                text_src=name_en or name_vi,
            )
        )

    description = course.get("description")
    if isinstance(description, dict):
        description_id = _non_empty_text(description.get("description_id"))
        text = _non_empty_text(description.get("text"))
        if description_id and text:
            units.append(
                _canonical_unit(
                    common,
                    unit_id=description_id,
                    unit_type="description",
                    description_id=description_id,
                    text_vi=text,
                    text_src=text,
                )
            )

    clos = course.get("clos")
    if isinstance(clos, list):
        for clo in clos:
            if not isinstance(clo, dict):
                continue
            clo_id = _non_empty_text(clo.get("clo_id"))
            text = _non_empty_text(clo.get("content")) or _non_empty_text(clo.get("clo_code"))
            if clo_id and text:
                units.append(
                    _canonical_unit(
                        common,
                        unit_id=clo_id,
                        unit_type="clo",
                        clo_id=clo_id,
                        text_vi=text,
                        text_src=text,
                    )
                )

    chapters = course.get("chapters")
    chapter_by_id: dict[str, dict[str, Any]] = {}
    if isinstance(chapters, list):
        for chapter in chapters:
            if not isinstance(chapter, dict):
                continue
            chapter_id = _non_empty_text(chapter.get("chapter_id"))
            title = _non_empty_text(chapter.get("title"))
            text = title or _non_empty_text(chapter.get("content_text")) or _non_empty_text(chapter.get("chapter_code"))
            if not chapter_id or not text:
                continue
            chapter_by_id[chapter_id] = chapter
            units.append(
                _canonical_unit(
                    common,
                    unit_id=chapter_id,
                    unit_type="chapter",
                    chapter_id=chapter_id,
                    chapter_title_vi=title or text,
                    text_vi=text,
                    text_src=text,
                )
            )

    lessons = course.get("lessons")
    if isinstance(lessons, list):
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            lesson_id = _non_empty_text(lesson.get("lesson_id"))
            text = _non_empty_text(lesson.get("title"))
            chapter_id = _non_empty_text(lesson.get("chapter_ref_id"))
            parent = chapter_by_id.get(chapter_id or "", {})
            parent_title = _non_empty_text(parent.get("title"))
            if lesson_id and text:
                units.append(
                    _canonical_unit(
                        common,
                        unit_id=lesson_id,
                        unit_type="lesson",
                        lesson_id=lesson_id,
                        chapter_id=chapter_id,
                        chapter_title_vi=parent_title,
                        text_vi=text,
                        text_src=text,
                    )
                )
    return units


def _contextual_cache_key(unit: Unit, prompt_version: str) -> str:
    context = {
        "prompt_version": prompt_version,
        "knowledge_block": unit.get("knowledge_block"),
        "course_name": unit.get("course_name_en") or unit.get("course_name_vi"),
        "chapter_title": unit.get("chapter_title_en") or unit.get("chapter_title_vi"),
        "text_src": unit["text_src"],
    }
    serialized = json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _translate_legacy_cache(
    units: list[Unit],
    translate_fn: TranslateFunction,
    cache: MutableMapping[str, Any],
) -> list[Unit]:
    """Preserve the old plain cache behavior for external callers during migration."""
    source_texts: list[str] = []
    for unit in units:
        text = unit.get("text_src")
        if not isinstance(text, str) or not text:
            raise ValueError("Mỗi unit phải có trường text_src là chuỗi không rỗng.")
        if text not in cache and text not in source_texts:
            source_texts.append(text)
    if source_texts:
        translated = translate_with_glossary(source_texts, translate_fn, load_glossary())
        if len(translated) != len(source_texts):
            raise ValueError("translate_fn phải trả về list có cùng số phần tử đầu vào.")
        cache.update(zip(source_texts, translated))
    return [{**unit, "text_en": cache[unit["text_src"]]} for unit in units]


def translate_units(
    units: list[Unit],
    translate_fn: TranslateFunction,
    *,
    translation_cache: MutableMapping[str, Any] | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> list[Unit]:
    """Translate units with glossary priority and a versioned contextual cache.

    A plain ``{text_src: text_en}`` cache remains supported for API backward
    compatibility. Production callers pass the v2 envelope created by
    :func:`pipeline.extract_translate.run_extract_translate.load_translation_cache`.
    """
    cache: MutableMapping[str, Any] = translation_cache if translation_cache is not None else {}
    if cache.get("schema_version") != "2.0":
        return _translate_legacy_cache(units, translate_fn, cache)

    entries = cache.setdefault("entries", {})
    legacy_entries = cache.setdefault("legacy_entries", {})
    if not isinstance(entries, dict) or not isinstance(legacy_entries, dict):
        raise ValueError("Translation cache v2 phải chứa entries và legacy_entries dạng object.")
    glossary = {key.strip(): value for key, value in load_glossary().items()}
    misses: list[tuple[str, str, Unit]] = []
    translations_by_key: dict[str, str] = {}

    for unit in units:
        text = unit.get("text_src")
        if not isinstance(text, str) or not text:
            raise ValueError("Mỗi unit phải có trường text_src là chuỗi không rỗng.")
        cache_key = _contextual_cache_key(unit, prompt_version)
        approved = glossary.get(text.strip())
        cached = entries.get(cache_key)
        if approved is not None:
            translations_by_key[cache_key] = approved
        elif isinstance(cached, dict) and isinstance(cached.get("text_en"), str):
            translations_by_key[cache_key] = cached["text_en"]
        elif isinstance(legacy_entries.get(text), str):
            translations_by_key[cache_key] = legacy_entries[text]
        elif cache_key not in {key for key, _, _ in misses}:
            misses.append((cache_key, text, unit))

    if misses:
        translated = translate_fn([text for _, text, _ in misses])
        if len(translated) != len(misses) or not all(isinstance(text, str) and text.strip() for text in translated):
            raise ValueError("translate_fn phải trả về list chuỗi không rỗng có cùng số phần tử đầu vào.")
        for (cache_key, _, _), text_en in zip(misses, translated):
            translations_by_key[cache_key] = text_en.strip()

    for unit in units:
        cache_key = _contextual_cache_key(unit, prompt_version)
        text_en = translations_by_key[cache_key]
        entries[cache_key] = {
            "text_src": unit["text_src"],
            "context": unit.get("course_name_en") or unit.get("course_name_vi"),
            "text_en": text_en,
        }

    translated_units: list[Unit] = []
    course_name_en: dict[str, str] = {}
    chapter_title_en: dict[str, str] = {}
    for unit in units:
        cache_key = _contextual_cache_key(unit, prompt_version)
        translated_unit = {**unit, "text_en": translations_by_key[cache_key]}
        translated_units.append(translated_unit)
        if unit.get("unit_type") == "name":
            course_name_en[unit["course_id"]] = translated_unit["text_en"]
        if unit.get("unit_type") == "chapter" and isinstance(unit.get("chapter_id"), str):
            chapter_title_en[unit["chapter_id"]] = translated_unit["text_en"]

    for translated_unit in translated_units:
        translated_unit["course_name_en"] = course_name_en.get(
            translated_unit["course_id"], translated_unit.get("course_name_en")
        )
        chapter_id = translated_unit.get("chapter_id")
        if isinstance(chapter_id, str):
            translated_unit["chapter_title_en"] = chapter_title_en.get(
                chapter_id, translated_unit.get("chapter_title_en")
            )
    # Validate canonical outputs. Legacy flat compatibility units intentionally
    # remain readable until their callers migrate to Layer 2 input.
    validated: list[Unit] = []
    for unit in translated_units:
        if unit.get("unit_id") in {
            unit.get("course_id"), unit.get("description_id"), unit.get("clo_id"), unit.get("chapter_id"), unit.get("lesson_id")
        }:
            validated.append(TranslatedUnit.model_validate(unit).model_dump(exclude_none=True))
        else:
            validated.append(unit)
    return validated


def mock_translate_fn(texts: list[str]) -> list[str]:
    return list(texts)
