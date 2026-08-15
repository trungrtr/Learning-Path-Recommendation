"""Normalize raw LLM JSON into the CTDT extraction contract."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.extract_ctdt.mo_hinh import CtdtDocument, HocPhanCtdt, NhomMon

LOGGER = logging.getLogger(__name__)


def _unwrap_payload(raw_payload: Any) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise ValueError("CTDT LLM output must be a JSON object.")
    for key in ("ctdt", "chuong_trinh_dao_tao", "program"):
        nested = raw_payload.get(key)
        if isinstance(nested, dict):
            return nested
    return raw_payload


def _dedupe_groups(items: list[Any]) -> list[NhomMon]:
    groups: list[NhomMon] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        group = NhomMon.model_validate(item)
        key = group.nhom_id.casefold() or group.ten_nhom.casefold()
        if key and key not in seen:
            groups.append(group)
            seen.add(key)
        elif key:
            LOGGER.warning("Bỏ nhóm CTDT trùng lặp: %s", group.nhom_id or group.ten_nhom)
    return groups


def _dedupe_courses(items: list[Any]) -> list[HocPhanCtdt]:
    courses: list[HocPhanCtdt] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        course = HocPhanCtdt.model_validate(item)
        key = course.ma_hp.casefold()
        if course.ma_hp and key not in seen:
            courses.append(course)
            seen.add(key)
        elif key:
            LOGGER.warning("Bỏ học phần CTDT trùng mã: %s", course.ma_hp)
    return courses


def normalize_ctdt_payload(raw_payload: Any) -> CtdtDocument:
    payload = _unwrap_payload(raw_payload)
    return CtdtDocument(
        schema_version="1.2",
        ma_ctdt=payload.get("ma_ctdt", ""),
        ten_nganh=payload.get("ten_nganh", ""),
        tong_so_tin_chi=payload.get("tong_so_tin_chi", 0),
        nhom_mon=_dedupe_groups(payload.get("nhom_mon") or []),
        hoc_phan=_dedupe_courses(payload.get("hoc_phan") or []),
    )

def validate_ctdt_document(doc: CtdtDocument) -> None:
    LOGGER.info("--- CTDT Validation Report ---")
    LOGGER.info("Tổng số tín chỉ chương trình: %s", doc.tong_so_tin_chi)
    LOGGER.info("Tổng số nhóm: %d", len(doc.nhom_mon))
    LOGGER.info("Tổng số học phần: %d", len(doc.hoc_phan))

    errors: list[str] = []
    nhom_ids: set[str] = set()
    duplicate_groups: set[str] = set()
    for group in doc.nhom_mon:
        if not group.nhom_id:
            errors.append("Có nhóm không có nhom_id.")
            continue
        if group.nhom_id in nhom_ids:
            duplicate_groups.add(group.nhom_id)
        nhom_ids.add(group.nhom_id)
    if duplicate_groups:
        errors.append(f"Trùng nhom_id: {sorted(duplicate_groups)}")

    hp_ids: set[str] = set()
    duplicate_courses: set[str] = set()
    for hp in doc.hoc_phan:
        if not hp.ma_hp:
            errors.append("Có học phần không có ma_hp.")
            continue
        if hp.ma_hp in hp_ids:
            duplicate_courses.add(hp.ma_hp)
        hp_ids.add(hp.ma_hp)
    if duplicate_courses:
        errors.append(f"Trùng ma_hp: {sorted(duplicate_courses)}")

    parent_ids = {group.nhom_cha_id for group in doc.nhom_mon if group.nhom_cha_id}
    non_leaf_course_groups: set[str] = set()
    so_tien_quyet = 0
    so_hoc_truoc = 0

    for n in doc.nhom_mon:
        if n.nhom_cha_id and n.nhom_cha_id not in nhom_ids:
            errors.append(f"Nhóm '{n.nhom_id}' tham chiếu nhom_cha_id '{n.nhom_cha_id}' không tồn tại.")

    outside_references: set[str] = set()
    for hp in doc.hoc_phan:
        so_tien_quyet += len(hp.tien_quyet)
        so_hoc_truoc += len(hp.hoc_truoc)

        if hp.nhom_id in parent_ids:
            non_leaf_course_groups.add(hp.nhom_id)
        if hp.nhom_id and hp.nhom_id not in nhom_ids:
            errors.append(f"Học phần '{hp.ma_hp}' tham chiếu nhom_id '{hp.nhom_id}' không tồn tại.")
        if not hp.nhom_id:
            errors.append(f"Học phần '{hp.ma_hp}' không xác định được nhóm.")
        if hp.hoc_ky is not None and not 1 <= hp.hoc_ky <= 12:
            errors.append(f"Học phần '{hp.ma_hp}' có hoc_ky ngoài khoảng hợp lệ: {hp.hoc_ky}.")

        for tq in hp.tien_quyet:
            if tq == hp.ma_hp:
                errors.append(f"Học phần '{hp.ma_hp}' tự lấy chính nó làm tiên quyết.")
            elif tq not in hp_ids:
                outside_references.add(tq)

        for ht in hp.hoc_truoc:
            if ht == hp.ma_hp:
                errors.append(f"Học phần '{hp.ma_hp}' tự lấy chính nó làm học trước.")
            elif ht not in hp_ids:
                outside_references.add(ht)

    if non_leaf_course_groups:
        errors.append(f"Học phần đang gán vào nhóm cha, chưa phải nhóm trực tiếp: {sorted(non_leaf_course_groups)}")
    overlap = {
        hp.ma_hp: sorted(set(hp.tien_quyet) & set(hp.hoc_truoc))
        for hp in doc.hoc_phan
        if set(hp.tien_quyet) & set(hp.hoc_truoc)
    }
    if overlap:
        LOGGER.warning("Các mã xuất hiện ở cả tiên quyết và học trước theo đúng PDF: %s", overlap)

    if outside_references:
        LOGGER.warning("Mã tham chiếu ngoài CTDT: %s", sorted(outside_references))
    LOGGER.info("Số quan hệ tiên quyết: %d", so_tien_quyet)
    LOGGER.info("Số quan hệ học trước: %d", so_hoc_truoc)
    LOGGER.info("--- End of Report ---")
    if errors:
        raise ValueError("CTDT validation failed: " + " | ".join(errors))
