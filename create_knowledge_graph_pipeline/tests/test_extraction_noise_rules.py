"""Regression tests for conservative Layer 1 structural noise filtering."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_course.mo_hinh import ExtractedDocument
from pipeline.extract_course.noise_rules import apply_lightweight_noise_rules


def _document() -> ExtractedDocument:
    return ExtractedDocument.model_validate(
        {
            "source_document": {
                "source_document_id": "SD_BS6002",
                "crawl_course_key": "BS6002",
            },
            "course": {"course_temp_id": "SD_BS6002_COURSE", "internal_course_code": "BS6002"},
            "description": {"description_temp_id": "SD_BS6002_DESC", "text": "Calculus description"},
            "clos": [{"clo_temp_id": "SD_BS6002_CLO1", "content": "Solve calculus problems"}],
            "chapters": [
                {"chapter_temp_id": "SD_BS6002_CH1", "title": "Double Integrals"},
                {"chapter_temp_id": "SD_BS6002_CH2", "title": "Hóa dược - ĐH K18"},
            ],
            "lessons": [
                {"lesson_temp_id": "SD_BS6002_L1", "title": "SQL"},
                {"lesson_temp_id": "SD_BS6002_L2", "title": "Công nghệ kỹ thuật cơ khí - ĐH K15"},
                {"lesson_temp_id": "SD_BS6002_L3", "title": "Chương trình đào tạo nâng cao"},
            ],
        }
    )


def test_high_confidence_cohort_noise_is_rejected_with_ids() -> None:
    cleaned, report = apply_lightweight_noise_rules(_document())

    assert [chapter.title for chapter in cleaned.chapters] == ["Double Integrals"]
    assert [lesson.title for lesson in cleaned.lessons] == ["SQL", "Chương trình đào tạo nâng cao"]
    rejected = [item for item in report.items if item.action == "rejected"]
    assert {item.record_id for item in rejected} == {"SD_BS6002_CH2", "SD_BS6002_L2"}
    assert all(item.reason == "programme_cohort_noise" for item in rejected)


def test_short_academic_content_is_kept_and_ambiguous_text_is_reviewed() -> None:
    cleaned, report = apply_lightweight_noise_rules(_document())

    assert any(lesson.title == "SQL" for lesson in cleaned.lessons)
    review = [item for item in report.items if item.action == "review_required_kept"]
    assert len(review) == 1
    assert review[0].record_id == "SD_BS6002_L3"


def test_disabled_rules_preserve_all_academic_records() -> None:
    original = _document()
    cleaned, report = apply_lightweight_noise_rules(original, enabled=False)

    assert cleaned.model_dump() == original.model_dump()
    assert report.items == []


def test_prompt_explicitly_rejects_programme_and_cohort_rows() -> None:
    prompt = (ROOT / "prompts" / "extraction.txt").read_text(encoding="utf-8")
    assert "ĐH K15" in prompt
    assert "Cohort K19" in prompt
    assert "không trích tên ngành" in prompt

