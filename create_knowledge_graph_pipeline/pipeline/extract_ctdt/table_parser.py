"""Deterministic table parser for CTDT PDF curriculum frames."""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

COURSE_RE = re.compile(r"^\s*(?P<stt>\d+)\s+(?P<ma>[A-Z]{2}\d{4})\s+(?P<body>.+)$")
COURSE_TAIL_RE = re.compile(
    r"(?P<name>.*?)\s+"
    r"(?P<tong>-?\d+(?:[,.]\d+)?)\s+"
    r"(?P<lt>-?\d+(?:[,.]\d+)?)\s+"
    r"(?P<th>-?\d+(?:[,.]\d+)?)\s+"
    r"(?P<btl>-?\d+(?:[,.]\d+)?)\s+"
    r"(?P<hoc_ky>[1-9])"
    r"(?:\s+(?P<deps>.*))?$"
)
COURSE_CODE_RE = re.compile(r"\b(?:[A-Z]{2}\d{4}|\d{6})\b")
NUMBER_RE = re.compile(r"-?\d+(?:[,.]\d+)?")
NUMBERED_GROUP_RE = re.compile(r"^(?P<id>[IVX]+(?:\.\d+)*)\s+(?P<rest>.+)$")
TOP_GROUP_RE = re.compile(r"^(?P<id>[IVX]+)\.\s+(?P<name>.+)$")
TECHNICAL_GROUP_RE = re.compile(r"^(?P<id>Tc\S+)\s*(?P<rest>.*)$")

DEPENDENCY_MIN_COLUMN = 150
HOC_TRUOC_COLUMN = 173


def parse_ctdt_pdf_table(path: Path) -> dict[str, Any]:
    """Extract CTDT schema fields from the rendered layout text of a PDF table."""

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF CTDT table parser requires pypdf. Install requirements.txt first.") from exc

    reader = PdfReader(str(path))
    groups: list[dict[str, Any]] = []
    group_ids: set[str] = set()
    courses: list[dict[str, Any]] = []

    ma_ctdt = ""
    ten_nganh = ""
    tong_so_tin_chi = 0.0
    current_numbered_group: str | None = None
    current_direct_group: str | None = None
    current_course: dict[str, Any] | None = None

    def add_group(
        nhom_id: str,
        ten_nhom: str,
        nhom_cha_id: str | None,
        loai_nhom: str,
        so_tin_chi_yeu_cau: float,
    ) -> None:
        if not nhom_id or nhom_id in group_ids:
            return
        groups.append(
            {
                "nhom_id": nhom_id,
                "ten_nhom": ten_nhom,
                "nhom_cha_id": nhom_cha_id,
                "loai_nhom": loai_nhom,
                "so_tin_chi_yeu_cau": so_tin_chi_yeu_cau,
            }
        )
        group_ids.add(nhom_id)

    for page in reader.pages:
        layout_text = page.extract_text(extraction_mode="layout") or ""
        for line in layout_text.splitlines():
            if not line.strip():
                continue
            stripped = line.strip()
            folded = _fold_text(stripped)

            if folded.startswith("ten nganh:"):
                ten_nganh = _after_colon(stripped)
                continue
            if folded.startswith("ma nganh:"):
                ma_ctdt = _after_colon(stripped)
                continue
            if folded.startswith("tong so tin chi"):
                numbers = NUMBER_RE.findall(stripped)
                if numbers:
                    tong_so_tin_chi = _to_float(numbers[-1])
                continue

            course_match = COURSE_RE.match(line)
            if course_match:
                course = _parse_course_line(line, course_match, current_direct_group or current_numbered_group or "")
                if course:
                    courses.append(course)
                    current_course = course
                continue

            if current_course and COURSE_CODE_RE.search(line) and len(line) >= DEPENDENCY_MIN_COLUMN:
                _append_dependencies_from_columns(line, current_course)
                continue
            current_course = None

            top_group = TOP_GROUP_RE.match(stripped)
            if top_group:
                nhom_id = top_group.group("id")
                add_group(nhom_id, top_group.group("name").strip(), None, "nhom_tong", 0.0)
                current_numbered_group = nhom_id
                current_direct_group = nhom_id
                continue

            numbered_group = NUMBERED_GROUP_RE.match(stripped)
            if numbered_group and "." in numbered_group.group("id"):
                nhom_id = numbered_group.group("id")
                ten_nhom, credits, loai_nhom = _parse_group_rest(numbered_group.group("rest"))
                add_group(nhom_id, ten_nhom, nhom_id.rsplit(".", 1)[0], loai_nhom or "nhom_tong", credits)
                current_numbered_group = nhom_id
                current_direct_group = nhom_id
                continue

            if folded.startswith("kien thuc bat buoc") and current_numbered_group:
                numbers = NUMBER_RE.findall(stripped)
                nhom_id = _required_group_id(current_numbered_group)
                add_group(
                    nhom_id,
                    "Kiến thức bắt buộc",
                    current_numbered_group,
                    "bat_buoc",
                    _to_float(numbers[0]) if numbers else 0.0,
                )
                current_direct_group = nhom_id
                continue

            technical_group = TECHNICAL_GROUP_RE.match(stripped)
            if technical_group and current_numbered_group:
                nhom_id = technical_group.group("id")
                numbers = NUMBER_RE.findall(technical_group.group("rest"))
                add_group(
                    nhom_id,
                    nhom_id,
                    current_numbered_group,
                    "tu_chon",
                    _to_float(numbers[0]) if numbers else 0.0,
                )
                current_direct_group = nhom_id

    if not groups or not courses:
        raise ValueError(f"No CTDT table data extracted from {path}")

    LOGGER.info("Parsed CTDT PDF table directly from %s", path.name)
    return {
        "schema_version": "1.2",
        "stage": "ctdt_llm_extraction",
        "ma_ctdt": ma_ctdt,
        "ten_nganh": ten_nganh,
        "tong_so_tin_chi": tong_so_tin_chi,
        "nhom_mon": groups,
        "hoc_phan": courses,
    }


def _parse_course_line(
    line: str,
    course_match: re.Match[str],
    current_group_id: str,
) -> dict[str, Any] | None:
    tail_match = COURSE_TAIL_RE.match(course_match.group("body"))
    if not tail_match:
        LOGGER.warning("Cannot parse CTDT course row: %s", line.strip())
        return None
    course = {
        "ma_hp": course_match.group("ma"),
        "nhom_id": current_group_id,
        "hoc_ky": int(tail_match.group("hoc_ky")),
        "tien_quyet": [],
        "hoc_truoc": [],
    }
    _append_dependencies_from_columns(line, course)
    return course


def _append_dependencies_from_columns(line: str, course: dict[str, Any]) -> None:
    for code_match in COURSE_CODE_RE.finditer(line):
        code = code_match.group().rstrip(",")
        column = code_match.start()
        if code == course["ma_hp"] or column < DEPENDENCY_MIN_COLUMN:
            continue
        target = course["tien_quyet"] if column < HOC_TRUOC_COLUMN else course["hoc_truoc"]
        if code not in target:
            target.append(code)


def _parse_group_rest(rest: str) -> tuple[str, float, str]:
    loai_nhom = ""
    folded = _fold_text(rest)
    if "co tu chon" in folded:
        loai_nhom = "tu_chon"
        rest = _remove_label_by_folded(rest, "co tu chon")
    elif "bat buoc" in folded:
        loai_nhom = "bat_buoc"
        rest = _remove_label_by_folded(rest, "bat buoc")

    numbers = list(NUMBER_RE.finditer(rest))
    if not numbers:
        return rest.strip(), 0.0, loai_nhom
    credit_match = numbers[-1]
    return rest[: credit_match.start()].strip(), _to_float(credit_match.group()), loai_nhom


def _remove_label_by_folded(text: str, folded_label: str) -> str:
    words = text.split()
    kept: list[str] = []
    index = 0
    while index < len(words):
        for size in range(min(3, len(words) - index), 0, -1):
            candidate = " ".join(words[index : index + size])
            if _fold_text(candidate) == folded_label:
                index += size
                break
        else:
            kept.append(words[index])
            index += 1
    return " ".join(kept)


def _required_group_id(parent_id: str) -> str:
    return f"{parent_id}.BB"


def _after_colon(text: str) -> str:
    return text.split(":", 1)[1].strip() if ":" in text else ""


def _to_float(value: str) -> float:
    return float(value.replace(",", "."))


def _fold_text(value: str) -> str:
    value = value.replace("Đ", "D").replace("đ", "d")
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").casefold()
