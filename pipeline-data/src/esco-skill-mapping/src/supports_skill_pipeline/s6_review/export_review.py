"""Bước 6 — Export candidates cho Human Review.

Xuất CSV và JSON cho reviewer đánh giá.
Mỗi candidate kèm theo câu hỏi bắt buộc:
  "Skill/knowledge này là NỀN TẢNG/BỔ TRỢ (SUPPORT) hay DẠY TRỰC TIẾP (TEACH)?"

Reviewer trả lời: ACCEPT (SUPPORT) hoặc REJECT (TEACH / không phù hợp).
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from ..models.candidate import ScoredCandidate

logger = logging.getLogger(__name__)


def export_for_review(
    course_code: str,
    course_name: str,
    candidates: list[ScoredCandidate],
    output_dir: str | Path,
) -> Path:
    """Xuất candidates cho Human Review dưới dạng CSV + JSON.

    Args:
        course_code: Mã học phần.
        course_name: Tên học phần.
        candidates: Danh sách ScoredCandidate từ Bước 5.
        output_dir: Thư mục output.

    Returns:
        Path tới file CSV đã tạo.
    """
    out_path = Path(output_dir)
    review_dir = out_path / "_review"
    review_dir.mkdir(parents=True, exist_ok=True)

    # --- Export CSV ---
    csv_path = review_dir / f"{course_code}_review.csv"

    fieldnames = [
        "course_code",
        "course_name",
        "candidate_rank",
        "skill_uri",
        "preferred_label",
        "skill_type",
        "support_concept_origin",
        "rrf_score",
        "escoxlmr_score",
        "evidence_score",
        "final_score",
        "evidence_text",
        "review_question",
        "review_status",
        "reviewer_note",
    ]

    review_question = (
        "Skill/knowledge này là NỀN TẢNG/BỔ TRỢ cho học phần (SUPPORT), "
        "hay thực chất là nội dung học phần DẠY TRỰC TIẾP (TEACH)? "
        "Trả lời: ACCEPT hoặc REJECT"
    )

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for cand in candidates:
            writer.writerow({
                "course_code": course_code,
                "course_name": course_name,
                "candidate_rank": cand.candidate_rank,
                "skill_uri": cand.skill_uri,
                "preferred_label": cand.skill_label,
                "skill_type": cand.skill_type,
                "support_concept_origin": "; ".join(cand.concept_origins),
                "rrf_score": round(cand.rrf_score, 4),
                "escoxlmr_score": round(cand.escoxlmr_score, 4),
                "evidence_score": round(cand.evidence_score, 4),
                "final_score": round(cand.final_score, 4),
                "evidence_text": cand.evidence_text,
                "review_question": review_question,
                "review_status": "pending",
                "reviewer_note": "",
            })

    # --- Export JSON (for programmatic import) ---
    json_path = review_dir / f"{course_code}_review.json"

    review_data = {
        "course_code": course_code,
        "course_name": course_name,
        "review_question": review_question,
        "candidates": [
            {
                "candidate_rank": cand.candidate_rank,
                "skill_uri": cand.skill_uri,
                "preferred_label": cand.skill_label,
                "skill_type": cand.skill_type,
                "support_concept_origin": cand.concept_origins,
                "scores": {
                    "rrf_score": round(cand.rrf_score, 4),
                    "escoxlmr_score": round(cand.escoxlmr_score, 4),
                    "evidence_score": round(cand.evidence_score, 4),
                    "final_score": round(cand.final_score, 4),
                },
                "evidence_text": cand.evidence_text,
                "review_status": "pending",
                "reviewer_note": "",
            }
            for cand in candidates
        ],
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(review_data, f, ensure_ascii=False, indent=2)

    logger.info(
        "Exported %d candidates for review: %s",
        len(candidates), csv_path,
    )

    return csv_path
