"""Bước 6 — Import kết quả Human Review.

Đọc kết quả review từ CSV hoặc JSON, trả về danh sách candidates
đã được phân loại ACCEPT/REJECT.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ReviewedCandidate:
    """Candidate đã qua Human Review."""
    course_code: str
    skill_uri: str
    preferred_label: str
    skill_type: str
    support_concept_origin: list[str]
    final_score: float
    evidence_text: str
    review_status: str      # "accepted" or "rejected"
    reviewer_note: str = ""


def import_review_results(
    review_path: str | Path,
) -> list[ReviewedCandidate]:
    """Import kết quả review từ CSV hoặc JSON.

    Args:
        review_path: Đường dẫn tới file review (CSV hoặc JSON).

    Returns:
        Danh sách ReviewedCandidate.
    """
    path = Path(review_path)

    if not path.exists():
        raise FileNotFoundError(f"Review file not found: {path}")

    if path.suffix == ".csv":
        return _import_csv(path)
    elif path.suffix == ".json":
        return _import_json(path)
    else:
        raise ValueError(f"Unsupported review file format: {path.suffix}")


def _import_csv(csv_path: Path) -> list[ReviewedCandidate]:
    """Import từ CSV."""
    results: list[ReviewedCandidate] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row.get("review_status", "pending").strip().lower()
            if status == "pending":
                continue  # Bỏ qua chưa review

            origins = row.get("support_concept_origin", "")
            concept_list = [c.strip() for c in origins.split(";") if c.strip()]

            results.append(ReviewedCandidate(
                course_code=row.get("course_code", ""),
                skill_uri=row.get("skill_uri", ""),
                preferred_label=row.get("preferred_label", ""),
                skill_type=row.get("skill_type", ""),
                support_concept_origin=concept_list,
                final_score=float(row.get("final_score", 0.0)),
                evidence_text=row.get("evidence_text", ""),
                review_status=status,
                reviewer_note=row.get("reviewer_note", ""),
            ))

    logger.info(
        "Imported %d reviewed candidates from CSV: %d accepted, %d rejected",
        len(results),
        sum(1 for r in results if r.review_status == "accepted"),
        sum(1 for r in results if r.review_status == "rejected"),
    )

    return results


def _import_json(json_path: Path) -> list[ReviewedCandidate]:
    """Import từ JSON."""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    course_code = data.get("course_code", "")
    results: list[ReviewedCandidate] = []

    for cand in data.get("candidates", []):
        status = cand.get("review_status", "pending").strip().lower()
        if status == "pending":
            continue

        results.append(ReviewedCandidate(
            course_code=course_code,
            skill_uri=cand.get("skill_uri", ""),
            preferred_label=cand.get("preferred_label", ""),
            skill_type=cand.get("skill_type", ""),
            support_concept_origin=cand.get("support_concept_origin", []),
            final_score=cand.get("scores", {}).get("final_score", 0.0),
            evidence_text=cand.get("evidence_text", ""),
            review_status=status,
            reviewer_note=cand.get("reviewer_note", ""),
        ))

    logger.info(
        "Imported %d reviewed candidates from JSON: %d accepted, %d rejected",
        len(results),
        sum(1 for r in results if r.review_status == "accepted"),
        sum(1 for r in results if r.review_status == "rejected"),
    )

    return results
