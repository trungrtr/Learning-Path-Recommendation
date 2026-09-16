"""Layer 005 — Evidence Builder: biến CourseData thành danh sách EvidenceUnit.

4 loại evidence: MO_TA, MUC_TIEU, CLO, BAI_HOC.
Luôn ưu tiên field _en cho extraction. Giữ field tiếng Việt trong text_vi.
Gắn metadata: loai_muc_tieu, content_richness, linked_clo.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from ..models.schemas import EvidenceUnit, CourseData
from ..utils.text import normalize_whitespace, is_grading_event

logger = logging.getLogger(__name__)

# [PATCH v3.0 — Evidence Quality Weighting]
EVIDENCE_WEIGHT_MAP: dict[tuple[str, Any], float] = {
    ("BAI_HOC",   "full"):                1.00,
    ("BAI_HOC",   "title_only"):          0.30,
    ("CLO",       "KIEN_THUC"):           0.90,
    ("CLO",       "KY_NANG"):             0.85,
    ("CLO",       "TU_CHU_TRACH_NHIEM"): 0.20,
    ("CLO",       None):                  0.85,
    ("MUC_TIEU",  "KIEN_THUC"):           0.70,
    ("MUC_TIEU",  "KY_NANG"):             0.65,
    ("MUC_TIEU",  "TU_CHU_TRACH_NHIEM"): 0.15,
    ("MO_TA",     None):                  0.25,
}

# [PATCH v3.0 — Boilerplate Sentence Filter]
BOILERPLATE_PATTERNS: list[str] = [
    r"proactive.{0,20}(learn|eager|attitude)",
    r"self.?disciplin",
    r"serious (learning|work) attitude",
    r"comprehensive(ly)? apply (knowledge|skills)",
    r"apply (acquired|comprehensive) knowledge",
    r"(practical|implement).{0,15}(information system|IT|technology project)",
    r"(accepting|receive).{0,10}(task|assignment|internship)",
    r"^writing report$",
    r"^planning and survey(ing)?$",
    r"^executing tasks?$",
    r"^(receiving|accepting) (the )?assignment$",
]

def is_boilerplate(text: str) -> bool:
    """Kiểm tra văn bản có phải câu rập khuôn/boilerplate không."""
    text_lower = text.strip().lower()
    return any(re.search(p, text_lower) for p in BOILERPLATE_PATTERNS)

def _post_process_unit(unit: EvidenceUnit) -> EvidenceUnit:
    """Gán evidence_weight và is_boilerplate cho EvidenceUnit."""
    source_type = unit.source_type
    subtype = unit.meta.get("loai_muc_tieu") or unit.meta.get("content_richness")
    weight = EVIDENCE_WEIGHT_MAP.get((source_type, subtype), 0.30)
    boilerplate = is_boilerplate(unit.text)

    return EvidenceUnit(
        evidence_id=unit.evidence_id,
        course_code=unit.course_code,
        source_type=unit.source_type,
        source_id=unit.source_id,
        text=unit.text,
        text_vi=unit.text_vi,
        meta=unit.meta,
        evidence_weight=weight,
        is_boilerplate=boilerplate,
    )

def compute_course_sparse_flag(units: list[EvidenceUnit], threshold: float = 0.60) -> bool:
    """Kiểm tra môn học có syllabus sparse (boilerplate ratio > threshold) không."""
    if not units:
        return True
    boilerplate_count = sum(1 for u in units if u.is_boilerplate)
    ratio = boilerplate_count / len(units)
    return ratio > threshold

def build_evidence(course: CourseData) -> list[EvidenceUnit]:
    """Build toàn bộ evidence units cho 1 học phần."""
    raw_units: list[EvidenceUnit] = []
    code = course.ma_hoc_phan

    raw_units.extend(_build_mo_ta(code, course))
    raw_units.extend(_build_muc_tieu(code, course))
    raw_units.extend(_build_clo(code, course))
    raw_units.extend(_build_bai_hoc(code, course))

    units = [_post_process_unit(u) for u in raw_units]

    logger.info(
        "Evidence built for %s: %d units (MO_TA=%d, MUC_TIEU=%d, CLO=%d, BAI_HOC=%d, boilerplate=%d)",
        code,
        len(units),
        sum(1 for u in units if u.source_type == "MO_TA"),
        sum(1 for u in units if u.source_type == "MUC_TIEU"),
        sum(1 for u in units if u.source_type == "CLO"),
        sum(1 for u in units if u.source_type == "BAI_HOC"),
        sum(1 for u in units if u.is_boilerplate),
    )
    return units

def _build_mo_ta(code: str, course: CourseData) -> list[EvidenceUnit]:
    text_en = normalize_whitespace(course.hoc_phan.mo_ta_tom_tat_en or "")
    text_vi = normalize_whitespace(course.hoc_phan.mo_ta_tom_tat or "")

    if not text_en:
        return []

    return [EvidenceUnit(
        evidence_id=f"{code}_MOTA_MAIN",
        course_code=code,
        source_type="MO_TA",
        source_id="M",
        text=text_en,
        text_vi=text_vi,
    )]

def _build_muc_tieu(code: str, course: CourseData) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    for mt in course.muc_tieu:
        text_en = normalize_whitespace(mt.noi_dung_en or "")
        text_vi = normalize_whitespace(mt.noi_dung or "")

        if not text_en or is_grading_event(text_en):
            continue

        source_id = mt.ma_muc_tieu or f"MT{len(units) + 1}"

        units.append(EvidenceUnit(
            evidence_id=f"{code}_MUCTIEU_{source_id}",
            course_code=code,
            source_type="MUC_TIEU",
            source_id=source_id,
            text=text_en,
            text_vi=text_vi,
            meta={"loai_muc_tieu": mt.loai_muc_tieu} if mt.loai_muc_tieu else {},
        ))
    return units

def _build_clo(code: str, course: CourseData) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    for clo in course.clo:
        text_en = normalize_whitespace(clo.noi_dung_en or "")
        text_vi = normalize_whitespace(clo.noi_dung or "")

        if not text_en or is_grading_event(text_en):
            continue

        source_id = clo.ma_cdr_goc   # L1, L2, L3...

        meta: dict = {}
        if clo.pi_so:
            meta["pi_so"] = clo.pi_so
        if clo.muc_do is not None:
            meta["muc_do"] = clo.muc_do

        text_lower = text_en.lower()
        if any(k in text_lower for k in ["learning attitude", "thái độ học tập", "self-disciplin", "tự giác", "cầu thị"]):
            clo_loai = "TU_CHU_TRACH_NHIEM"
        elif any(k in text_lower for k in ["knowledge", "understand", "explain", "describe", "kiến thức", "hiểu", "trình bày", "nắm vững"]):
            clo_loai = "KIEN_THUC"
        else:
            clo_loai = "KY_NANG"
        meta["loai_muc_tieu"] = clo_loai

        units.append(EvidenceUnit(
            evidence_id=f"{code}_CLO_{source_id}",
            course_code=code,
            source_type="CLO",
            source_id=source_id,
            text=text_en,
            text_vi=text_vi,
            meta=meta,
        ))
    return units

def _build_bai_hoc(code: str, course: CourseData) -> list[EvidenceUnit]:
    units: list[EvidenceUnit] = []
    for idx, bh in enumerate(course.bai_hoc, start=1):
        content_en = normalize_whitespace(bh.noi_dung_tom_tat_en or "")
        title_en = normalize_whitespace(bh.ten_bai_en or "")
        title_vi = normalize_whitespace(bh.ten_bai or "")

        if content_en:
            text = f"{title_en}. {content_en}" if title_en else content_en
            richness = "full"
        elif title_en:
            text = title_en
            richness = "title_only"
        else:
            continue

        if is_grading_event(text):
            continue

        source_id = f"L{idx:02d}"

        meta: dict = {
            "content_richness": richness,
        }
        if bh.ma_clo:
            meta["linked_clo"] = bh.ma_clo

        units.append(EvidenceUnit(
            evidence_id=f"{code}_BAIHOC_{source_id}",
            course_code=code,
            source_type="BAI_HOC",
            source_id=source_id,
            text=text,
            text_vi=title_vi,
            meta=meta,
        ))
    return units
