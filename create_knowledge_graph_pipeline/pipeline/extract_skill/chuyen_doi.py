from typing import Any

from .mo_hinh import DescriptionBlock, Layer3SkillDocument


def enrich_document_with_skills(layer2_doc: dict[str, Any], raw_skills: list[str]) -> Layer3SkillDocument:
    """Lưu skill phrase LLM và các trường nguồn để audit."""
    course_info = layer2_doc.get("course", {})
    # Mô tả học phần
    desc_raw = layer2_doc.get("description", {})
    description = DescriptionBlock(
        description_id=desc_raw.get("description_id"),
        course_ref_id=desc_raw.get("course_ref_id"),
        text=desc_raw.get("text"),
    ) if isinstance(desc_raw, dict) and desc_raw.get("text") else None
    # Chuẩn đầu ra
    clos = [item.get("content") or item.get("clo_code") or "" for item in layer2_doc.get("clos", [])]
    # Chương
    chapters = [item.get("title") or item.get("chapter_code") or "" for item in layer2_doc.get("chapters", [])]
    # Bài học – deduplicate giữ thứ tự
    lessons_raw = layer2_doc.get("lessons", [])
    seen_lessons: set[str] = set()
    lessons: list[str] = []
    for item in lessons_raw:
        title = item.get("title") or "" if isinstance(item, dict) else str(item) if item else ""
        if title and title not in seen_lessons:
            lessons.append(title)
            seen_lessons.add(title)
    return Layer3SkillDocument(
        course_id=course_info.get("course_id", ""),
        course_code=course_info.get("course_code"),
        internal_course_code=course_info.get("internal_course_code"),
        name_vi=course_info.get("name_vi"),
        name_en=course_info.get("name_en"),
        description=description,
        clos=clos,
        chapters=chapters,
        lessons=lessons,
        keyword_skills=raw_skills,
    )

