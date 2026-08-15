from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from pipeline.kg_export.exporter import export_kg


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _fixtures(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    canonical = tmp_path / "canonical"
    translated = tmp_path / "translated"
    matches = tmp_path / "matches"
    output = tmp_path / "kg"
    _write_json(canonical / "C1.json", {
        "schema_version": "2.3", "stage": "layer_2_canonical_course",
        "course": {"course_id": "C1", "internal_course_code": "BS1", "name_vi": "Đại số"},
        "description": {"description_id": "D1", "text": "Mô tả"},
        "clos": [{"clo_id": "O1", "content": "Tính định thức"}],
        "chapters": [{"chapter_id": "H1", "title": "Ma trận"}],
        "lessons": [{"lesson_id": "L1", "chapter_ref_id": "H1", "title": "Định thức"}],
    })
    units = [
        ("C1", "name", "Đại số", "Linear Algebra", {}),
        ("D1", "description", "Mô tả", "Description", {"description_id": "D1"}),
        ("O1", "clo", "Tính định thức", "Calculate determinants", {"clo_id": "O1"}),
        ("H1", "chapter", "Ma trận", "Matrices", {"chapter_id": "H1"}),
        ("L1", "lesson", "Định thức", "Determinants", {"lesson_id": "L1", "chapter_id": "H1"}),
    ]
    _write_json(translated / "BS1.json", [
        {
            "course_id": "C1", "unit_id": unit_id, "unit_type": unit_type,
            "text_vi": vi, "text_src": vi, "text_en": en, **ids,
        }
        for unit_id, unit_type, vi, en, ids in units
    ])
    _write_json(matches / "BS1.json", {
        "schema_version": "1.0", "stage": "course_skill_output",
        "calibration_status": "experimental", "limitations": ["Gold Dataset pending"],
        "course_id": "C1", "internal_course_code": "BS1",
        "matched_skills": [{
            "skill_id": "S1", "skill_uri": "https://data.europa.eu/esco/skill/S1",
            "skill_label": "calculate determinants", "relation_type": "teaches",
            "retrieval_score": 0.7, "rerank_score": 0.8, "validation_confidence": 0.9,
            "evidence": [{"unit_id": "L1", "unit_type": "lesson", "quote": "Determinants"}],
        }],
    })
    return canonical, translated, matches, output


def test_export_builds_nodes_relationships_and_evidence_csv(tmp_path: Path) -> None:
    canonical, translated, matches, output = _fixtures(tmp_path)
    export = export_kg(canonical, translated, matches, output)

    assert export.courses[0].name_en == "Linear Algebra"
    assert export.course_skill_relationships[0].evidence_unit_ids == ["L1"]
    assert all((output / name).exists() for name in ["courses.csv", "course_skill_relationships.csv", "kg_export.json"])
    with (output / "course_skill_relationships.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["evidence_unit_ids"]) == ["L1"]


def test_export_rejects_unknown_evidence_unit(tmp_path: Path) -> None:
    canonical, translated, matches, output = _fixtures(tmp_path)
    payload = json.loads((matches / "BS1.json").read_text(encoding="utf-8"))
    payload["matched_skills"][0]["evidence"][0]["unit_id"] = "UNKNOWN"
    _write_json(matches / "BS1.json", payload)

    with pytest.raises(ValueError, match="Unknown evidence"):
        export_kg(canonical, translated, matches, output)
