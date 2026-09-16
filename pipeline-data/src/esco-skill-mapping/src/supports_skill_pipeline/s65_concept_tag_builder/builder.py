"""Bước 6.5 — Concept Tag Builder.

Nhận:
- support_concepts (list[str]) từ S2
- scored_candidates (list[ScoredCandidate]) đã qua S5.5 verification
- course_code, course_name

Xuất:
- _concept_tags.json trong thư mục output chứa:
  - concept_tags: danh sách ConceptTag nodes (deduplicated)
  - has_concept_edges: HocPhan → ConceptTag (role="support")
  - evidence_for_edges: ConceptTag → KyNangESCO

Phân loại loai:
- "knowledge" trong ESCO skillType → loai = "foundational"
- Còn lại → heuristic dựa trên keyword trong concept text
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ..models.candidate import ScoredCandidate

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic phân loại ConceptTag
# ---------------------------------------------------------------------------

_COGNITIVE_KEYWORDS = {
    "thinking", "tư duy", "logic", "reasoning", "analysis", "phân tích",
    "problem solving", "giải quyết vấn đề", "critical", "abstract",
    "computational", "algorithmic", "pattern recognition", "decomposition",
    "systematic", "analytical", "evaluate", "đánh giá", "synthesis",
    "attention to detail", "precision", "troubleshooting", "debugging",
}

_INTERPERSONAL_KEYWORDS = {
    "teamwork", "làm việc nhóm", "communication", "giao tiếp",
    "collaboration", "hợp tác", "leadership", "lãnh đạo",
    "presentation", "thuyết trình", "negotiation", "đàm phán",
    "empathy", "conflict resolution", "mentoring",
}

_METHODOLOGICAL_KEYWORDS = {
    "research", "nghiên cứu", "methodology", "phương pháp",
    "planning", "lập kế hoạch", "project management", "quản lý",
    "documentation", "tài liệu", "workflow", "process",
    "time management", "organization", "procedural",
    "persistence", "self-learning", "tự học",
}


def _classify_concept(concept_text: str, esco_skill_type: str) -> str:
    """Phân loại ConceptTag thành 1 trong 4 loại.

    Returns:
        "foundational" | "cognitive" | "interpersonal" | "methodological"
    """
    # Nếu ESCO skill type là knowledge → foundational
    if esco_skill_type and "knowledge" in esco_skill_type.lower():
        return "foundational"

    text_lower = concept_text.lower()

    # Check interpersonal trước (thường rõ ràng nhất)
    for kw in _INTERPERSONAL_KEYWORDS:
        if kw in text_lower:
            return "interpersonal"

    # Check cognitive
    for kw in _COGNITIVE_KEYWORDS:
        if kw in text_lower:
            return "cognitive"

    # Check methodological
    for kw in _METHODOLOGICAL_KEYWORDS:
        if kw in text_lower:
            return "methodological"

    # Default: cognitive (kỹ năng bổ trợ thường là tư duy)
    return "cognitive"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_concept_tags(
    course_code: str,
    support_concepts: list[str],
    scored_candidates: list[ScoredCandidate],
    output_dir: str | Path,
) -> None:
    """Tạo _concept_tags.json cho 1 course.

    Side-output thuần túy — không ảnh hưởng SupportSkillRecord.

    Args:
        course_code: Mã học phần.
        support_concepts: Danh sách raw concepts từ S2.
        scored_candidates: Danh sách candidates đã accepted (sau S5.5).
        output_dir: Thư mục output gốc.
    """
    if not support_concepts:
        return

    out_path = Path(output_dir)
    course_dir = out_path / course_code
    course_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Bước 1: Normalize & Dedup raw concepts → ConceptTag nodes
    # ------------------------------------------------------------------
    concept_tags: dict[str, dict] = {}
    for concept in support_concepts:
        key = concept.strip().lower()
        if not key or len(key) < 2:
            continue
        if key not in concept_tags:
            concept_tags[key] = {
                "text": concept.strip(),
                "normalized": key,
                "loai": "",  # Sẽ được gán ở bước 2
            }

    # ------------------------------------------------------------------
    # Bước 2: Tìm skill type từ accepted candidates để phân loại loai
    # ------------------------------------------------------------------
    # Map concept → skill_type dựa trên concept_origins
    concept_skill_types: dict[str, str] = {}
    for cand in scored_candidates:
        for origin in cand.concept_origins:
            origin_key = origin.strip().lower()
            if origin_key and origin_key not in concept_skill_types:
                concept_skill_types[origin_key] = cand.skill_type or ""

    # Gán loai cho từng ConceptTag
    for key, tag in concept_tags.items():
        esco_type = concept_skill_types.get(key, "")
        tag["loai"] = _classify_concept(tag["text"], esco_type)

    # ------------------------------------------------------------------
    # Bước 3: Build HAS_CONCEPT edges (HocPhan → ConceptTag)
    # ------------------------------------------------------------------
    has_concept_edges: list[dict] = [
        {
            "course_code": course_code,
            "concept_tag": tag["normalized"],
            "role": "support",
        }
        for tag in concept_tags.values()
    ]

    # ------------------------------------------------------------------
    # Bước 4: Build EVIDENCE_FOR edges (ConceptTag → KyNangESCO)
    # ------------------------------------------------------------------
    evidence_for_edges: list[dict] = []
    seen_pairs: set[tuple[str, str]] = set()

    for cand in scored_candidates:
        for origin in cand.concept_origins:
            origin_key = origin.strip().lower()
            pair = (origin_key, cand.skill_uri)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            evidence_for_edges.append({
                "concept_tag": origin_key,
                "esco_uri": cand.skill_uri,
                "esco_label": cand.skill_label,
                "confidence": round(cand.final_score, 6),
                "pipeline_source": "supports_M5",
            })

    # ------------------------------------------------------------------
    # Bước 5: Xuất _concept_tags.json
    # ------------------------------------------------------------------
    output_data = {
        "course_code": course_code,
        "concept_tags": [
            {
                "text": t["text"],
                "normalized": t["normalized"],
                "loai": t["loai"],
            }
            for t in concept_tags.values()
        ],
        "has_concept_edges": has_concept_edges,
        "evidence_for_edges": evidence_for_edges,
        "statistics": {
            "total_concept_tags": len(concept_tags),
            "total_has_concept_edges": len(has_concept_edges),
            "total_evidence_for_edges": len(evidence_for_edges),
        },
    }

    with open(course_dir / "_concept_tags.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(
        "S6.5: Exported %d concept tags (%d EVIDENCE_FOR edges) to %s/",
        len(concept_tags), len(evidence_for_edges), course_dir,
    )
