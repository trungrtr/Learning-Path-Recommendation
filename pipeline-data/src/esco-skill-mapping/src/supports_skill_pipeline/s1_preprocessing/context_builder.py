"""Bước 1 — Data Cleaning & Course Context Aggregation.

Gộp Description + Objectives + CLO thành một Course Context thống nhất, đã làm sạch.
Không dùng LLM ở bước này.

Input: Course data (JSON contract).
Output: course_context (str) — text thuần, sẵn sàng cho LLM và retrieval.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..utils.text import clean_text, normalize_whitespace

logger = logging.getLogger(__name__)


def _load_course_json(course_code: str, contract_dir: Path) -> dict[str, Any]:
    """Load và merge dữ liệu course từ các file JSON contract.

    Tìm file theo pattern: {contract_dir}/{course_code}/*.json
    hoặc {contract_dir}/{course_code}.json
    """
    # Thử tìm trong thư mục hoc_phan (cấu trúc chuẩn)
    course_dir = contract_dir / "hoc_phan" / course_code
    if not course_dir.is_dir():
        # Fallback về cấu trúc phẳng
        course_dir = contract_dir / course_code

    if course_dir.is_dir():
        merged: dict[str, Any] = {}
        for json_file in sorted(course_dir.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                key = json_file.stem.split("__")[-1]
                
                # Unwrap 'records' structure if present
                if isinstance(data, dict) and "records" in data:
                    merged[key] = data["records"]
                    merged[f"{key}_source_hash"] = data.get("source_hash")
                elif isinstance(data, list):
                    merged[key] = data
                elif isinstance(data, dict):
                    merged.update(data)
        return merged

    # Thử load file đơn
    single_file = contract_dir / f"{course_code}.json"
    if single_file.exists():
        with open(single_file, "r", encoding="utf-8") as f:
            return json.load(f)

    raise FileNotFoundError(
        f"Course data not found for {course_code} in {contract_dir}"
    )


def _extract_description(course_data: dict[str, Any]) -> str:
    """Trích xuất description từ course data."""
    # Ưu tiên field tiếng Anh
    hp = course_data.get("hoc_phan", course_data)
    desc_en = hp.get("mo_ta_tom_tat_en", "")
    desc_vi = hp.get("mo_ta_tom_tat", "")
    desc = hp.get("description", "")

    return clean_text(desc_en or desc or desc_vi)


def _extract_objectives(course_data: dict[str, Any]) -> list[str]:
    """Trích xuất objectives từ course data."""
    objectives = []

    # Thử field "muc_tieu" (format Vietnam)
    muc_tieu_list = course_data.get("muc_tieu", [])
    if isinstance(muc_tieu_list, list):
        for mt in muc_tieu_list:
            if isinstance(mt, dict):
                text = mt.get("noi_dung_en", "") or mt.get("noi_dung", "")
                if text:
                    objectives.append(clean_text(text))
            elif isinstance(mt, str):
                objectives.append(clean_text(mt))

    # Thử field "objectives" (format English)
    obj_list = course_data.get("objectives", [])
    if isinstance(obj_list, list) and not objectives:
        for obj in obj_list:
            if isinstance(obj, str):
                objectives.append(clean_text(obj))

    return [o for o in objectives if o]


def _extract_clo(course_data: dict[str, Any]) -> list[str]:
    """Trích xuất CLO từ course data."""
    clos = []

    # Thử field "chuan_dau_ra" hoặc "clo" (format Vietnam)
    cdr_list = course_data.get("chuan_dau_ra") or course_data.get("clo", [])
    if isinstance(cdr_list, list):
        for clo in cdr_list:
            if isinstance(clo, dict):
                text = clo.get("noi_dung_en", "") or clo.get("noi_dung", "")
                if text:
                    clos.append(clean_text(text))
            elif isinstance(clo, str):
                clos.append(clean_text(clo))

    # Thử field "CLO" (format English)
    clo_list = course_data.get("CLO", [])
    if isinstance(clo_list, list) and not clos:
        for clo in clo_list:
            if isinstance(clo, str):
                clos.append(clean_text(clo))

    return [c for c in clos if c]


def _extract_course_name(course_data: dict[str, Any]) -> str:
    """Trích xuất tên course."""
    hp = course_data.get("hoc_phan", course_data)
    name_en = hp.get("ten_en", "")
    name_vi = hp.get("ten_vi", "")
    name = hp.get("course_name", "")
    return clean_text(name_en or name or name_vi)


def build_course_context(
    course_code: str,
    contract_dir: str | Path,
) -> tuple[str, str]:
    """Gộp Description + Objectives + CLO thành Course Context thống nhất.

    Args:
        course_code: Mã học phần.
        contract_dir: Thư mục chứa data contract.

    Returns:
        Tuple (course_name, course_context):
        - course_name: Tên học phần.
        - course_context: Text thuần đã chuẩn hóa, sẵn sàng cho LLM.

    Raises:
        FileNotFoundError: Nếu không tìm thấy dữ liệu course.
    """
    contract_path = Path(contract_dir)
    course_data = _load_course_json(course_code, contract_path)

    course_name = _extract_course_name(course_data)
    description = _extract_description(course_data)
    objectives = _extract_objectives(course_data)
    clos = _extract_clo(course_data)

    # Validate — log warning nếu thiếu, không crash
    missing_fields = []
    if not description:
        missing_fields.append("description")
    if not objectives:
        missing_fields.append("objectives")
    if not clos:
        missing_fields.append("CLO")

    if missing_fields:
        logger.warning(
            "Course %s: missing fields: %s — proceeding with available data.",
            course_code,
            ", ".join(missing_fields),
        )

    # Build context string
    parts: list[str] = []

    if course_name:
        parts.append(f"Course: {course_name}.")

    if description:
        parts.append(f"Description: {description}")

    if objectives:
        obj_text = " ".join(objectives)
        parts.append(f"Objectives: {obj_text}")

    if clos:
        clo_text = " ".join(clos)
        parts.append(f"CLO: {clo_text}")

    course_context = "\n".join(parts)

    if not course_context.strip():
        logger.error("Course %s: no content available after cleaning.", course_code)

    logger.info(
        "Context built for %s: %d chars (desc=%d, obj=%d, clo=%d)",
        course_code,
        len(course_context),
        len(description),
        len(objectives),
        len(clos),
    )

    return course_name, course_context
