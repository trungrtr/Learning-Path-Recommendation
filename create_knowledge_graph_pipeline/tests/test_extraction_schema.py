import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.extract_course.chuyen_doi import build_document


class FakeExtraction:
    def __init__(self, extraction_class, extraction_text, attributes=None):
        self.extraction_class = extraction_class
        self.extraction_text = extraction_text
        self.attributes = attributes or {}


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


def test_extraction_maps_all_core_fields_and_chapter_reference(tmp_path):
    markdown_path = tmp_path / "sample.md"
    markdown_path.write_text("dummy", encoding="utf-8")
    doc = build_document(
        markdown_path,
        [
            FakeExtraction(
                "course",
                "Linear Algebra",
                {
                    "course_code": "HP4827",
                    "name_vi": "Đại số tuyến tính",
                    "description_text": "Mô tả học phần.",
                },
            ),
            FakeExtraction(
                "clo",
                "Apply matrix methods",
                {"clo_code": "C1", "content": "Apply matrix methods", "order_index": 1},
            ),
            FakeExtraction(
                "chapter",
                "Chapter 1: Matrices",
                {
                    "chapter_code": "1",
                    "title": "Matrices",
                    "content_text": "Matrix fundamentals",
                    "order_index": 1,
                },
            ),
            FakeExtraction(
                "lesson",
                "Quadratic forms",
                {"chapter_code": "1", "title": "Quadratic forms", "order_index": 42},
            ),
        ],
        "BS6001",
        "test-model",
    )

    assert doc.schema_version == "1.2"
    assert doc.source_document.model_dump() == {
        "crawl_course_key": "BS6001",
        "source_document_id": doc.source_document.source_document_id,
    }
    assert doc.course.course_code == "HP4827"
    assert doc.course.internal_course_code == "BS6001"
    assert doc.description.text == "Mô tả học phần."
    assert doc.clos[0].content == "Apply matrix methods"
    assert doc.chapters[0].content_text == "Matrix fundamentals"
    assert doc.lessons[0].model_dump(exclude_none=True) == {
        "lesson_temp_id": doc.lessons[0].lesson_temp_id,
        "chapter_ref_temp_id": doc.chapters[0].chapter_temp_id,
        "title": "Quadratic forms",
        "order_index": 42,
    }
    schema = json.loads((ROOT / "schemas" / "layer1_source_extraction_schema.json").read_text(encoding="utf-8"))
    _assert_schema_shape(doc.model_dump(), schema)
