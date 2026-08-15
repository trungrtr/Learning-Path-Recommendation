"""Unit tests cho bước tách unit và cache dịch của Layer 3."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_translate.course_units import extract_units, translate_units
from pipeline.extract_translate.run_extract_translate import load_translation_cache, run


def test_extract_units_preserves_expected_order_and_name_source() -> None:
    course = {
        "course_id": "COURSE_1",
        "name_vi": "Đại số tuyến tính",
        "name_en": "Linear Algebra",
        "clos": ["CLO 1", "CLO 2"],
        "chapters": ["Chương 1"],
    }

    units = extract_units(course)

    assert [(unit["unit_type"], unit["unit_id"]) for unit in units] == [
        ("name", "name_1"),
        ("clo", "clo_1"),
        ("clo", "clo_2"),
        ("chapter", "chapter_1"),
    ]
    assert units[0]["text_vi"] == "Đại số tuyến tính"
    assert units[0]["text_src"] == "Linear Algebra"


def test_extract_units_reads_nested_canonical_course() -> None:
    units = extract_units(
        {
            "course": {"course_id": "COURSE_1", "internal_course_code": "C1", "name_vi": "Course"},
            "description": {"description_id": "COURSE_1_DESC", "text": "Description"},
            "clos": [{"clo_id": "COURSE_1_CLO1", "content": "CLO content"}],
            "chapters": [{"chapter_id": "COURSE_1_CH1", "title": "Chapter title"}],
            "lessons": [
                {"lesson_id": "COURSE_1_L1", "chapter_ref_id": "COURSE_1_CH1", "title": "Lesson title"}
            ],
        }
    )

    assert [(unit["unit_type"], unit["unit_id"]) for unit in units] == [
        ("name", "COURSE_1"),
        ("description", "COURSE_1_DESC"),
        ("clo", "COURSE_1_CLO1"),
        ("chapter", "COURSE_1_CH1"),
        ("lesson", "COURSE_1_L1"),
    ]
    assert units[-1]["chapter_id"] == "COURSE_1_CH1"
    assert units[-1]["chapter_title_vi"] == "Chapter title"


def test_extract_units_skips_missing_or_empty_fields() -> None:
    assert extract_units({"name_vi": "Thiếu mã"}) == []
    assert extract_units({"course_id": "COURSE_1", "name_vi": " ", "clos": ["", None]}) == []


def test_translate_units_batches_only_unique_cache_misses() -> None:
    calls: list[list[str]] = []

    def fake_translate(texts: list[str]) -> list[str]:
        calls.append(texts)
        return [f"EN:{text}" for text in texts]

    units = [
        {"course_id": "C1", "unit_type": "clo", "unit_id": "clo_1", "text_vi": "A", "text_src": "A"},
        {"course_id": "C1", "unit_type": "chapter", "unit_id": "chapter_1", "text_vi": "A", "text_src": "A"},
        {"course_id": "C2", "unit_type": "keyword", "unit_id": "keyword_1", "text_vi": "B", "text_src": "B"},
        {"course_id": "C2", "unit_type": "name", "unit_id": "name_1", "text_vi": "C", "text_src": "C"},
    ]
    cache = {"C": "Cached C"}

    translated = translate_units(units, fake_translate, translation_cache=cache)

    assert calls == [["A", "B"]]
    assert [unit["text_en"] for unit in translated] == ["EN:A", "EN:A", "EN:B", "Cached C"]
    assert cache == {"A": "EN:A", "B": "EN:B", "C": "Cached C"}


def test_run_writes_one_translated_file_per_course_and_keeps_cache_outside_output(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "BS6001.json").write_text(
        '{"course_id":"COURSE_1","internal_course_code":"BS6001","name_vi":"Đại số"}',
        encoding="utf-8",
    )
    output_dir = tmp_path / "output"
    cache_path = tmp_path / "cache" / "vi_en.json"

    courses, units, translated = run(
        input_dir,
        output_dir,
        cache_path,
        lambda texts: [f"EN:{text}" for text in texts],
    )

    assert (courses, units, translated) == (1, 1, 1)
    assert [path.name for path in output_dir.glob("*.json")] == ["BS6001.json"]
    assert cache_path.exists()


def test_contextual_cache_separates_same_text_in_different_courses() -> None:
    calls: list[list[str]] = []

    def fake_translate(texts: list[str]) -> list[str]:
        calls.append(texts)
        return [f"EN:{text}" for text in texts]

    units = [
        {
            "course_id": "C1",
            "unit_id": "C1_CH1",
            "unit_type": "chapter",
            "chapter_id": "C1_CH1",
            "course_name_vi": "Giải tích",
            "chapter_title_vi": "Đạo hàm",
            "text_vi": "Đạo hàm",
            "text_src": "Đạo hàm",
        },
        {
            "course_id": "C2",
            "unit_id": "C2_CH1",
            "unit_type": "chapter",
            "chapter_id": "C2_CH1",
            "course_name_vi": "Tài chính",
            "chapter_title_vi": "Đạo hàm",
            "text_vi": "Đạo hàm",
            "text_src": "Đạo hàm",
        },
    ]
    cache = {"schema_version": "2.0", "prompt_version": "v2", "entries": {}, "legacy_entries": {}}

    translated = translate_units(units, fake_translate, translation_cache=cache, prompt_version="v2")

    assert calls == [["Đạo hàm", "Đạo hàm"]]
    assert len(cache["entries"]) == 2
    assert all(unit["text_en"] == "EN:Đạo hàm" for unit in translated)


def test_load_translation_cache_migrates_plain_mapping(tmp_path: Path) -> None:
    cache_path = tmp_path / "legacy.json"
    cache_path.write_text('{"Đạo hàm":"Derivative"}', encoding="utf-8")

    cache = load_translation_cache(cache_path, "v2")

    assert cache["schema_version"] == "2.0"
    assert cache["legacy_entries"] == {"Đạo hàm": "Derivative"}
    assert cache["entries"] == {}
