from __future__ import annotations

import json
from pathlib import Path

from pipeline.extract_ctdt.chuyen_doi import normalize_ctdt_payload
from pipeline.extract_ctdt.mo_hinh import CtdtDocument
from pipeline.extract_ctdt.table_parser import parse_ctdt_pdf_table
from pipeline.run_pipeline import STAGES


ROOT = Path(__file__).resolve().parents[1]


def test_ctdt_contract_matches_min_schema() -> None:
    schema = json.loads((ROOT / "schemas" / "ctdt_schema_min.json").read_text(encoding="utf-8"))

    assert set(schema) == set(CtdtDocument.model_fields)


def test_normalize_ctdt_payload_dedupes_courses_and_preserves_dependencies() -> None:
    document = normalize_ctdt_payload(
        {
            "ma_ctdt": "HTTT",
            "ten_nganh": "Hệ thống thông tin",
            "nhom_mon": [
                {"nhom_id": "CN", "ten_nhom": "Chuyên ngành", "tong_so_tin": 30},
                {"nhom_id": "CN", "ten_nhom": "Chuyên ngành", "so_tin_chi_yeu_cau": 30},
            ],
            "hoc_phan": [
                {
                    "ma_hp": "IT6006",
                    "nhom_id": "CN",
                    "hoc_ky": 5,
                    "tien_quyet": ["IT6002", "IT6002"],
                    "hoc_truoc": None,
                },
                {"ma_hp": "IT6006", "nhom_id": "CN", "hoc_ky": 5},
            ],
        }
    )

    assert document.ma_ctdt == "HTTT"
    assert len(document.nhom_mon) == 1
    assert len(document.hoc_phan) == 1
    assert document.hoc_phan[0].tien_quyet == ["IT6002"]
    assert document.hoc_phan[0].hoc_truoc == []


def test_parse_ctdt_pdf_table_keeps_groups_semesters_and_dependency_columns() -> None:
    pdf_path = ROOT / "data" / "00_input" / "CTDT" / "CTDT_HTTT.pdf"

    payload = parse_ctdt_pdf_table(pdf_path)
    groups = {group["nhom_id"]: group for group in payload["nhom_mon"]}
    courses = {course["ma_hp"]: course for course in payload["hoc_phan"]}

    assert payload["schema_version"] == "1.2"
    assert payload["tong_so_tin_chi"] == 139
    assert groups["I.1"]["ten_nhom"] == "Ngoài khung"
    assert groups["I.2"]["ten_nhom"] == "Lý luận chính trị"
    assert groups["TcHTTT4"]["nhom_cha_id"] == "II.1"
    assert courses["IT6010"]["nhom_id"] == "TcHTTT4"
    assert courses["LP6013"]["hoc_ky"] == 5
    assert courses["LP6004"]["hoc_ky"] == 6
    assert courses["LP6003"]["hoc_ky"] == 7
    assert courses["IT6067"]["tien_quyet"] == []
    assert courses["IT6067"]["hoc_truoc"] == ["IT6015"]
    assert courses["IT6018"]["tien_quyet"] == ["IT6015"]
    assert courses["IT6018"]["hoc_truoc"] == []
    assert courses["IT6044"]["tien_quyet"] == ["IT6002"]


def test_ctdt_packet_is_not_in_default_course_pipeline() -> None:
    assert "extract_course" in STAGES
    assert "extract_ctdt" not in STAGES
