"""Layer 00: Ingestion & Validation.

Đọc 4 file JSON cho mỗi học phần từ thư mục contract,
validate tính toàn vẹn của dữ liệu và lọc bỏ các học phần không hợp lệ.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..models.schemas import (
    CourseData,
    HocPhanSchema,
    CloSchema,
    BaiHocSchema,
    MucTieuSchema,
)

logger = logging.getLogger(__name__)

# --- Validator ---

@dataclass
class ValidationResult:
    course_code: str
    is_valid: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

def validate_course(course: CourseData, config: Any = None) -> ValidationResult:
    result = ValidationResult(course_code=course.ma_hoc_phan)

    # 1. source_hash consistency
    hashes = course.source_hashes
    unique_hashes = {v for v in hashes.values() if v}
    if len(unique_hashes) > 1:
        result.warnings.append(f"source_hash mismatch: {hashes}")

    # 2. ma_hoc_phan khớp
    if course.hoc_phan.ma_hoc_phan != course.ma_hoc_phan:
        result.errors.append(
            f"ma_hoc_phan mismatch: folder={course.ma_hoc_phan}, "
            f"hoc_phan.json={course.hoc_phan.ma_hoc_phan}"
        )
        result.is_valid = False

    # 3. CLO có nội dung
    empty_clo = [
        c.ma_cdr_goc for c in course.clo
        if not (c.noi_dung_en or "").strip()
    ]
    if empty_clo:
        result.warnings.append(f"CLO thiếu noi_dung_en: {empty_clo}")

    # 4. Mục tiêu có loai_muc_tieu hợp lệ
    valid_loai = {"KIEN_THUC", "KY_NANG", "TU_CHU_TRACH_NHIEM"}
    invalid_mt = [
        (mt.ma_muc_tieu, mt.loai_muc_tieu)
        for mt in course.muc_tieu
        if mt.loai_muc_tieu and mt.loai_muc_tieu not in valid_loai
    ]
    if invalid_mt:
        result.warnings.append(f"Mục tiêu có loai_muc_tieu không hợp lệ: {invalid_mt}")

    # 5. Bài học có tên
    empty_bh = sum(1 for bh in course.bai_hoc if not (bh.ten_bai_en or "").strip())
    if empty_bh > 0:
        result.warnings.append(f"{empty_bh}/{len(course.bai_hoc)} bài học thiếu ten_bai_en")

    # 6. Ít nhất 1 nguồn evidence có text
    has_any_text = (
        bool(course.hoc_phan.mo_ta_tom_tat_en)
        or any((c.noi_dung_en or "").strip() for c in course.clo)
        or any((mt.noi_dung_en or "").strip() for mt in course.muc_tieu)
        or any((bh.ten_bai_en or "").strip() for bh in course.bai_hoc)
    )
    if not has_any_text:
        result.errors.append("Không có nguồn evidence nào có nội dung tiếng Anh")
        result.is_valid = False

    # 7. Filter theo từ khóa
    if config and hasattr(config, "course_filter") and getattr(config.course_filter, "enabled", False):
        ten_vi = (course.hoc_phan.ten_vi or "").lower()
        for kw in getattr(config.course_filter, "ignored_keywords", []):
            if kw in ten_vi:
                result.errors.append(f"Loại bỏ môn học chính trị/lý luận: chứa từ khóa '{kw}'")
                result.is_valid = False
                break

    if result.errors:
        logger.error("Course %s: INVALID — %s", course.ma_hoc_phan, result.errors)
    elif result.warnings:
        logger.warning("Course %s: valid with warnings — %s", course.ma_hoc_phan, result.warnings)
    else:
        logger.debug("Course %s: valid", course.ma_hoc_phan)

    return result

# --- Loader ---

def _read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_single_course(ma_hoc_phan: str, contract_dir: Path | str) -> CourseData:
    base = Path(contract_dir) / "hoc_phan" / ma_hoc_phan
    hp_path = base / f"{ma_hoc_phan}__hoc_phan.json"
    clo_path = base / f"{ma_hoc_phan}__clo.json"
    bh_path = base / f"{ma_hoc_phan}__bai_hoc.json"
    mt_path = base / f"{ma_hoc_phan}__muc_tieu.json"

    for p in (hp_path, clo_path, bh_path, mt_path):
        if not p.exists():
            raise FileNotFoundError(f"Data contract file missing: {p}")

    hp_raw = _read_json(hp_path)
    clo_raw = _read_json(clo_path)
    bh_raw = _read_json(bh_path)
    mt_raw = _read_json(mt_path)

    source_hashes = {
        "hoc_phan": hp_raw.get("source_hash", "") if isinstance(hp_raw, dict) else "",
        "clo": clo_raw.get("source_hash", "") if isinstance(clo_raw, dict) else "",
        "bai_hoc": bh_raw.get("source_hash", "") if isinstance(bh_raw, dict) else "",
        "muc_tieu": mt_raw.get("source_hash", "") if isinstance(mt_raw, dict) else "",
    }

    if isinstance(hp_raw, list):
        hp_raw = hp_raw[0] if hp_raw else {}
    elif isinstance(hp_raw, dict) and "records" in hp_raw:
        records = hp_raw["records"]
        hp_raw = records[0] if records else {}

    if isinstance(clo_raw, dict) and "records" in clo_raw:
        clo_raw = clo_raw["records"]
    elif not isinstance(clo_raw, list):
        clo_raw = [clo_raw]

    if isinstance(bh_raw, dict) and "records" in bh_raw:
        bh_raw = bh_raw["records"]
    elif not isinstance(bh_raw, list):
        bh_raw = [bh_raw]

    if isinstance(mt_raw, dict) and "records" in mt_raw:
        mt_raw = mt_raw["records"]
    elif not isinstance(mt_raw, list):
        mt_raw = [mt_raw]

    hoc_phan = HocPhanSchema.model_validate(hp_raw)
    clo_list = [CloSchema.model_validate(item) for item in clo_raw if item]
    bh_list = [BaiHocSchema.model_validate(item) for item in bh_raw if item]
    mt_list = [MucTieuSchema.model_validate(item) for item in mt_raw if item]

    course = CourseData(
        ma_hoc_phan=ma_hoc_phan,
        hoc_phan=hoc_phan,
        clo=clo_list,
        bai_hoc=bh_list,
        muc_tieu=mt_list,
        source_hashes=source_hashes,
    )
    
    logger.info("Loaded course %s: %d CLO, %d bài học, %d mục tiêu",
                ma_hoc_phan, len(clo_list), len(bh_list), len(mt_list))
    return course

def discover_and_load_all(contract_dir: Path | str) -> list[CourseData]:
    contract_dir = Path(contract_dir)
    hp_dir = contract_dir / "hoc_phan"

    if not hp_dir.is_dir():
        logger.warning("hoc_phan directory not found: %s", hp_dir)
        return []

    courses: list[CourseData] = []
    for course_dir in sorted(hp_dir.iterdir()):
        if not course_dir.is_dir():
            continue
        ma = course_dir.name
        try:
            course = load_single_course(ma, contract_dir)
            courses.append(course)
        except (FileNotFoundError, Exception) as exc:
            logger.warning("Skipping %s: %s", ma, exc)

    logger.info("Discovered %d courses in %s", len(courses), contract_dir)
    return courses
