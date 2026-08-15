from __future__ import annotations

import csv
import json
from pathlib import Path

from pipeline.kg_export.ctdt_exporter import export_ctdt_kg
from pipeline.kg_export.models import CtdtKGExport
from pipeline.run_ctdt_pipeline import build_stage_command, selected_stages


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_ctdt_kg_contract_matches_schema() -> None:
    schema = json.loads((ROOT / "schemas" / "ctdt_kg_schema.json").read_text(encoding="utf-8"))

    assert set(schema["properties"]) == set(CtdtKGExport.model_fields)


def test_ctdt_export_builds_program_groups_courses_and_dependencies(tmp_path: Path) -> None:
    ctdt_dir = tmp_path / "ctdt"
    output = tmp_path / "kg_ready"
    _write_json(
        ctdt_dir / "HTTT.json",
        {
            "schema_version": "1.0",
            "stage": "ctdt_llm_extraction",
            "ma_ctdt": "HTTT",
            "ten_nganh": "He thong thong tin",
            "nhom_mon": [
                {"nhom_id": "CS", "ten_nhom": "Co so nganh", "tong_so_tin": 30},
                {"nhom_id": "CN", "ten_nhom": "Chuyen nganh", "nhom_cha_id": "CS", "tong_so_tin": 12},
            ],
            "hoc_phan": [
                {
                    "ma_hp": "IT6006",
                    "nhom_id": "CN",
                    "hoc_ky": 5,
                    "tien_quyet": ["IT6002"],
                    "hoc_truoc": ["BS6001"],
                }
            ],
        },
    )

    export = export_ctdt_kg(ctdt_dir, output)

    assert export.programs[0].program_id == "CTDT_HTTT"
    assert len(export.groups) == 2
    assert export.group_relationships[0].relationship_type == "HAS_SUBGROUP"
    assert export.course_relationships[0].ma_hp == "IT6006"
    assert {item.relationship_type for item in export.course_dependency_relationships} == {
        "RECOMMENDS_PRIOR_COURSE",
        "REQUIRES_COURSE",
    }
    assert all(
        (output / name).exists()
        for name in [
            "ctdt_programs.csv",
            "ctdt_groups.csv",
            "ctdt_course_relationships.csv",
            "ctdt_course_dependency_relationships.csv",
            "ctdt_kg_export.json",
        ]
    )
    with (output / "ctdt_course_relationships.csv").open(encoding="utf-8-sig", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["ma_hp"] == "IT6006"
    assert row["hoc_ky"] == "5"


def test_ctdt_pipeline_orchestrator_keeps_course_pipeline_separate() -> None:
    assert selected_stages("extract_ctdt", "kg_export_ctdt") == ("extract_ctdt", "kg_export_ctdt")
    command = build_stage_command("kg_export_ctdt", Path("config.yaml"))
    assert command[-3:] == ["pipeline.kg_export.ctdt", "--config", "config.yaml"]
