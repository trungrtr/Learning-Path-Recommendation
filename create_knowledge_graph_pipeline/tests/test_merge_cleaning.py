import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_course.mo_hinh import ExtractedDocument
from pipeline.merge.cleaning import clean_extracted_document
from pipeline.merge.__main__ import merge_group, validate_canonical_course


def _assert_schema_shape(actual, schema):
    if isinstance(schema, dict):
        assert isinstance(actual, dict)
        assert set(actual) == set(schema)
        for key, value in schema.items():
            _assert_schema_shape(actual[key], value)
    elif isinstance(schema, list) and schema:
        assert isinstance(actual, list)
        for item in actual:
            _assert_schema_shape(item, schema[0])

def test_cleaning_removes_garbage_clos_and_exact_duplicates():
    raw = _minimal_source("SD_1", "Description")
    raw["lessons"] = [
        {"lesson_temp_id": "SD_1_L1", "title": "Lesson one", "order_index": 1}
    ]
    document = ExtractedDocument.model_validate(raw)
    document.lessons.append(deepcopy(document.lessons[0]))

    cleaned, report = clean_extracted_document(document)

    assert len(cleaned.lessons) == 1
    assert any(item["reason"] == "exact_duplicate" for item in report["items"])


def test_cleaning_removes_garbage_clos():
    raw = _minimal_source("SD_1", "Description")
    raw["clos"] = [
        {"clo_temp_id": "SD_1_CLO1", "clo_code": "C1", "content": "C1", "order_index": 1},
        {
            "clo_temp_id": "SD_1_CLO2",
            "clo_code": "C2",
            "content": "Apply a method",
            "order_index": 2,
        },
    ]
    cleaned, report = clean_extracted_document(ExtractedDocument.model_validate(raw))

    assert not any(clo.content == clo.clo_code for clo in cleaned.clos)
    assert any(item["reason"] == "garbage_clo" for item in report["items"])


def test_merge_defensively_rejects_legacy_cohort_noise() -> None:
    raw = _minimal_source("SD_1", "Description")
    raw["lessons"] = [
        {"lesson_temp_id": "SD_1_L1", "title": "SQL", "order_index": 1},
        {
            "lesson_temp_id": "SD_1_L2",
            "title": "Công nghệ kỹ thuật cơ khí - ĐH K15",
            "order_index": 2,
        },
    ]

    cleaned, report = clean_extracted_document(ExtractedDocument.model_validate(raw))

    assert [lesson.title for lesson in cleaned.lessons] == ["SQL"]
    assert any(item["reason"] == "programme_cohort_noise" for item in report["items"])


def test_cleaning_deduplicates_continuation_suffix_without_using_order() -> None:
    raw = _minimal_source("SD_1", "Description")
    raw["lessons"] = [
        {"lesson_temp_id": "SD_1_L1", "title": "Double Integrals", "order_index": 1},
        {"lesson_temp_id": "SD_1_L2", "title": "Double Integrals (tiếp)", "order_index": 9},
    ]

    cleaned, report = clean_extracted_document(ExtractedDocument.model_validate(raw))

    assert len(cleaned.lessons) == 1
    assert any(item["reason"] == "exact_duplicate" for item in report["items"])


def test_orphan_lesson_is_kept_and_reported_as_warning(tmp_path) -> None:
    raw = _minimal_source("SD_1", "Description")
    raw["lessons"] = [
        {"lesson_temp_id": "SD_1_L1", "title": "Independent topic", "order_index": 1}
    ]
    path = tmp_path / "source.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    merged = merge_group([path])
    issues = validate_canonical_course(merged)

    assert len(merged["lessons"]) == 1
    assert merged["lessons"][0]["chapter_ref_id"] is None
    assert issues == [
        {
            "type": "orphan_lesson",
            "severity": "warning",
            "field": "lessons.chapter_ref_id",
            "lesson_id": merged["lessons"][0]["lesson_id"],
        }
    ]


def _minimal_source(source_id: str, description: str) -> dict:
    return {
        "schema_version": "1.2",
        "stage": "layer_1_source_extraction",
        "source_document": {"crawl_course_key": "BS6001", "source_document_id": source_id},
        "course": {
            "course_temp_id": f"{source_id}_COURSE",
            "course_code": "HP1",
            "internal_course_code": "BS6001",
            "name_vi": "Course",
            "name_en": None,
            "credits": {"total": 3, "theory": None, "practice": None, "self_study": None},
            "department": None,
            "knowledge_block": None,
            "education_level": None,
        },
        "description": {"description_temp_id": f"{source_id}_DESC", "text": description},
        "clos": [],
        "chapters": [],
        "lessons": [],
    }


def test_merge_unions_cleaned_children_and_keeps_both_sources(tmp_path):
    first = _minimal_source("SD_1", "Description from source one.")
    second = _minimal_source("SD_2", "Longer description from source two.")
    first["course"].update({"department": "Department A"})
    second["course"].update({"education_level": "Undergraduate"})
    first["clos"] = [{"clo_temp_id": "SD_1_CLO1", "clo_code": "C1", "content": "Apply a method", "order_index": 1}]
    second["clos"] = [
        {"clo_temp_id": "SD_2_CLO1", "clo_code": "C1", "content": "Apply a method", "order_index": 1},
        {"clo_temp_id": "SD_2_CLO2", "clo_code": "C2", "content": "Evaluate results", "order_index": 2},
    ]
    first["chapters"] = [{"chapter_temp_id": "SD_1_CH1", "chapter_code": "1", "title": "Chapter one", "content_text": "Chapter one content", "order_index": 1}]
    second["chapters"] = [
        {"chapter_temp_id": "SD_2_CH1", "chapter_code": "1", "title": "Chapter one", "content_text": "Chapter one content", "order_index": 1},
        {"chapter_temp_id": "SD_2_CH2", "chapter_code": "2", "title": "Chapter two", "content_text": "Chapter two content", "order_index": 2},
    ]
    first["lessons"] = [
        {
            "lesson_temp_id": "SD_1_L1",
            "chapter_ref_temp_id": "SD_1_CH1",
            "title": "Lesson one",
            "order_index": 1,
        }
    ]
    second["lessons"] = [
        {
            "lesson_temp_id": "SD_2_L1",
            "chapter_ref_temp_id": "SD_2_CH1",
            "title": "Lesson one",
            "order_index": 1,
        },
        {
            "lesson_temp_id": "SD_2_L2",
            "chapter_ref_temp_id": "SD_2_CH2",
            "title": "Lesson two",
            "order_index": 2,
        },
    ]
    first_path, second_path = tmp_path / "source_1.json", tmp_path / "source_2.json"
    first_path.write_text(json.dumps(first), encoding="utf-8")
    second_path.write_text(json.dumps(second), encoding="utf-8")

    merged = merge_group([first_path, second_path])

    assert merged["schema_version"] == "2.3"
    assert merged["course"]["department"] == "Department A"
    assert merged["course"]["education_level"] == "Undergraduate"
    assert len(merged["clos"]) == 2
    assert len(merged["chapters"]) == 2
    assert len(merged["lessons"]) == 2
    assert set(merged["description"]) == {"description_id", "text"}
    assert "Description from source one." in merged["description"]["text"]
    assert "Longer description from source two." in merged["description"]["text"]
    assert set(merged["lessons"][0]) == {
        "lesson_id",
        "chapter_ref_id",
        "title",
        "order_index",
    }
    assert merged["lessons"][0]["chapter_ref_id"] == merged["chapters"][0]["chapter_id"]
    assert set(merged) == {
        "schema_version",
        "stage",
        "course",
        "description",
        "clos",
        "chapters",
        "lessons",
    }
    schema = json.loads((ROOT / "schemas" / "layer2_canonical_course_schema.json").read_text(encoding="utf-8"))
    _assert_schema_shape(merged, schema)
    assert validate_canonical_course(merged) == []
