"""
Xuất dữ liệu data contract cho esco-skill-mapping.

Module DUY NHẤT trong extract-translate-data được phép ghi vào thư mục
data contract (data/exports/skill_mapping_input/). Không chứa logic
ESCO/mapping nào — chỉ chuyển đổi từ schema nội bộ sang format contract.

Data contract format (mỗi học phần = 4 file JSON):
    <ma_hoc_phan>__hoc_phan.json
    <ma_hoc_phan>__muc_tieu.json
    <ma_hoc_phan>__clo.json
    <ma_hoc_phan>__bai_hoc.json

Mỗi file chứa `source_hash` để esco-skill-mapping phát hiện thay đổi.
"""

import json
import logging
import re
from pathlib import Path

from shared.file_io import write_json, get_content_hash

logger = logging.getLogger(__name__)

_DEFAULT_EXPORT_DIR = Path("../../contract")


def export_single_course(course_data: dict, export_dir: Path | str | None = None) -> None:
    """Xuất 4 file JSON cho 1 học phần theo data contract.

    Parameters
    ----------
    course_data:
        Dict chứa key: ma_hoc_phan, hoc_phan (dict), muc_tieu_hoc_phan (list),
        clo (list), bai_hoc (list) — output từ M3 assemble/translate.
    export_dir:
        Thư mục export. Mặc định: data/exports/skill_mapping_input/
    """
    export_dir = Path(export_dir) if export_dir else _DEFAULT_EXPORT_DIR

    ma = course_data.get("ma_hoc_phan", "")
    if not ma:
        logger.warning("Skipping course without ma_hoc_phan")
        return

    export_dir = export_dir / "hoc_phan" / ma
    export_dir.mkdir(parents=True, exist_ok=True)

    # ── hoc_phan ─────────────────────────────────────────────────────────
    hp_data = course_data.get("hoc_phan", {})
    if isinstance(hp_data, dict):
        hp_data["source_hash"] = get_content_hash(hp_data)
    write_json(export_dir / f"{ma}__hoc_phan.json", hp_data)

    # ── muc_tieu ─────────────────────────────────────────────────────────
    mt_data = course_data.get("muc_tieu_hoc_phan", []) or []
    mt_export = []
    for item in mt_data:
        if isinstance(item, dict):
            mt_export.append(item)
        else:
            # Pydantic model → dict
            mt_export.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
    # Attach source_hash to the list
    mt_with_hash = {"records": mt_export, "source_hash": get_content_hash(mt_export)}
    write_json(export_dir / f"{ma}__muc_tieu.json", mt_with_hash)

    # ── clo ──────────────────────────────────────────────────────────────
    clo_data = course_data.get("clo", []) or []
    clo_export = []
    for item in clo_data:
        if isinstance(item, dict):
            clo_export.append(item)
        else:
            clo_export.append(item.model_dump() if hasattr(item, "model_dump") else dict(item))
    clo_with_hash = {"records": clo_export, "source_hash": get_content_hash(clo_export)}
    write_json(export_dir / f"{ma}__clo.json", clo_with_hash)

    # ── bai_hoc ──────────────────────────────────────────────────────────
    bh_data = course_data.get("bai_hoc", []) or []
    bh_export = []
    for item in bh_data:
        if isinstance(item, dict):
            item_dict = dict(item)
        else:
            item_dict = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            
        if item_dict.get("ten_bai"):
            item_dict["ten_bai"] = re.sub(r'^(?:Bài|Chương|Phần)\s*\d+\s*[\:\.\-]*\s*', '', item_dict["ten_bai"], flags=re.IGNORECASE).strip()
        if item_dict.get("ten_bai_en"):
            item_dict["ten_bai_en"] = re.sub(r'^(?:Lab|Lesson|Chapter|Part)\s*\d+\s*[\:\.\-]*\s*', '', item_dict["ten_bai_en"], flags=re.IGNORECASE).strip()
            
        bh_export.append(item_dict)
    bh_with_hash = {"records": bh_export, "source_hash": get_content_hash(bh_export)}
    write_json(export_dir / f"{ma}__bai_hoc.json", bh_with_hash)

    logger.info("Exported data contract for %s → %s", ma, export_dir)


def export_batch(courses: list[dict], export_dir: Path | str | None = None) -> None:
    """Xuất data contract cho nhiều học phần.

    Parameters
    ----------
    courses:
        List of course dicts (output từ M3).
    export_dir:
        Thư mục export.
    """
    for course in courses:
        try:
            export_single_course(course, export_dir)
        except Exception as exc:
            ma = course.get("ma_hoc_phan", "???")
            logger.error("Failed to export %s: %s", ma, exc)
