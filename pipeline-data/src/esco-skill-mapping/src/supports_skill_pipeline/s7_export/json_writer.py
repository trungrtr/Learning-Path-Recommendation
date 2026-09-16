"""Bước 7 — JSON Writer.

Ghi output JSON theo cấu trúc giống data_teaches_skill/:
  data_support_skill/
  ├── {course_code}/
  │   ├── _summary.json           # Tổng hợp course
  │   ├── skill__{label_slug}.json  # Chi tiết từng skill
  │   └── knowledge__{label_slug}.json
  ├── _cypher/
  │   └── {course_code}.cypher
  └── _review/
      └── {course_code}_review.csv
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..models.record import SupportSkillRecord
from ..utils.text import slugify_label

logger = logging.getLogger(__name__)


def write_records(
    records: list[SupportSkillRecord],
    output_dir: str | Path,
) -> None:
    """Ghi từng record thành 1 file JSON riêng biệt.

    Tổ chức theo: {output_dir}/{course_code}/{type}__{label_slug}.json

    Args:
        records: Danh sách SupportSkillRecord đã accepted.
        output_dir: Thư mục output gốc.
    """
    out_path = Path(output_dir)

    for record in records:
        course_dir = out_path / record.course_code
        course_dir.mkdir(parents=True, exist_ok=True)

        # Tạo filename: skill_type prefix + label slug
        if record.skill_type and "knowledge" in record.skill_type.lower():
            prefix = "knowledge"
        else:
            prefix = "skill"

        label_slug = slugify_label(record.preferred_label)
        filename = f"{prefix}__{label_slug}.json"
        filepath = course_dir / filename

        # Ghi JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

    if records:
        logger.info(
            "Written %d records to %s",
            len(records), out_path,
        )


def write_summary(
    course_code: str,
    course_name: str,
    records: list[SupportSkillRecord],
    output_dir: str | Path,
) -> None:
    """Ghi file _summary.json cho 1 course.

    Args:
        course_code: Mã học phần.
        course_name: Tên học phần.
        records: Danh sách records cho course này.
        output_dir: Thư mục output gốc.
    """
    out_path = Path(output_dir)
    course_dir = out_path / course_code
    course_dir.mkdir(parents=True, exist_ok=True)

    # Phân loại
    skills = [r for r in records if "knowledge" not in (r.skill_type or "").lower()]
    knowledge = [r for r in records if "knowledge" in (r.skill_type or "").lower()]

    summary = {
        "course_code": course_code,
        "course_title": course_name,
        "relation_type": "SUPPORTS_SKILL",
        "statistics": {
            "total_records": len(records),
            "skill_count": len(skills),
            "knowledge_count": len(knowledge),
        },
        "skills": [
            {
                "preferred_label": r.preferred_label,
                "esco_uri": r.esco_uri,
                "final_score": round(r.final_score, 4),
                "support_concept_origin": r.support_concept_origin,
                "review_status": r.review_status,
            }
            for r in skills
        ],
        "knowledge": [
            {
                "preferred_label": r.preferred_label,
                "esco_uri": r.esco_uri,
                "final_score": round(r.final_score, 4),
                "support_concept_origin": r.support_concept_origin,
                "review_status": r.review_status,
            }
            for r in knowledge
        ],
    }

    summary_path = course_dir / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(
        "Written summary for %s: %d records (%d skill, %d knowledge)",
        course_code, len(records), len(skills), len(knowledge),
    )
