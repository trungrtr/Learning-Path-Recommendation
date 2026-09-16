"""Export translated CTDT records grouped by training programme.

This entrypoint consumes only data/translated_entities/ctdt/*.json. It does
not extract, translate, or modify any previous pipeline output.
"""

from pathlib import Path
from typing import Any

from pipeline.m3.materialize_ctdt import materialize_ctdt_batch
from shared.file_io import read_json, read_yaml_config, write_json





def _contract_course_code(code: str, source_stream: str | None) -> str:
    """Keep the original code and mark supplementary courses with ``_BS``."""
    if source_stream != "hoc_phan_bo_sung" or code.endswith("_BS"):
        return code
    return f"{code}_BS"


def _write_program_contract(
    program: dict[str, Any],
    contract_root: Path,
    course_records: dict[str, dict[str, Any]],
) -> None:
    program_root = contract_root / "ctdt" / str(program["ma_ctdt"])
    program_root.mkdir(parents=True, exist_ok=True)
    program_courses = []
    supplement_courses = []
    missing_courses = []
    for item in program.get("courses", []):
        source_stream = item.get("source_stream")
        original_code = item.get("ma_hoc_phan")
        contract_code = (
            _contract_course_code(original_code, source_stream)
            if original_code
            else original_code
        )
        course_summary = {
            "ma_hoc_phan": contract_code,
            "ma_hoc_phan_goc": original_code,
            "memberships": item.get("memberships", []),
            "source_stream": source_stream,
            "fallback_used": item.get("fallback_used", False),
            "resolution_status": item.get("resolution_status"),
            "data_available": isinstance(item.get("course"), dict),
        }
        program_courses.append(course_summary)
        if item.get("source_stream") == "hoc_phan_bo_sung":
            supplement_courses.append(course_summary)
        if item.get("resolution_status") == "unresolved":
            membership = (item.get("memberships") or [{}])[0]
            missing_courses.append({
                "ma_hoc_phan": item.get("ma_hoc_phan"),
                "ten_hoc_phan": membership.get("ten_hoc_phan"),
                "ten_hoc_phan_en": membership.get("ten_hoc_phan_en"),
                "nhom_id": membership.get("nhom_id"),
                "ma_phan": membership.get("ma_phan"),
            })

    write_json(program_root / f"CTDT_{program['ma_ctdt']}.json", {
        "ma_ctdt": program["ma_ctdt"],
        "crawl_course_key": program["crawl_course_key"],
        "program": program.get("program", {}),
        "courses": program_courses,
        "supplement_courses": supplement_courses,
        "missing_courses": missing_courses,
        "resolution_summary": program.get("resolution_summary", {}),
        "unresolved_course_codes": program.get("unresolved_course_codes", []),
    })

    lines = [
        f"# Missing courses - CTDT {program['ma_ctdt']}",
        "",
        "This report lists CTDT courses without a matching record in "
        "hoc_phan or hoc_phan_bo_sung.",
        "",
        f"Total missing: {len(missing_courses)}",
        f"Resolved from hoc_phan_bo_sung: {len(supplement_courses)}",
        "",
    ]
    if missing_courses:
        lines.extend([
            "| Course code | Vietnamese name | English name | Group | Section |",
            "|---|---|---|---|---|",
        ])
        for course in missing_courses:
            lines.append(
                f"| {course['ma_hoc_phan'] or ''} | "
                f"{course['ten_hoc_phan'] or ''} | "
                f"{course['ten_hoc_phan_en'] or ''} | "
                f"{course['nhom_id'] or ''} | {course['ma_phan'] or ''} |"
            )
    else:
        lines.append("No missing courses.")
    (program_root / "MISSING_COURSES.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    for item in program.get("courses", []):
        course = item.get("course")
        if not isinstance(course, dict):
            continue
        original_code = item["ma_hoc_phan"]
        code = _contract_course_code(original_code, item.get("source_stream"))
        hashes = course.get("source_hashes", [])
        source_hash = hashes[0] if hashes else course.get("content_hash", "")
        course_data = {
            **course.get("hoc_phan", {}),
            "ma_hoc_phan": code,
            "ma_hoc_phan_goc": original_code,
            "crawl_course_key": course.get("crawl_course_key"),
            "source_hash": source_hash,
            "ctdt_memberships": item.get("memberships", []),
            "ctdt_source_stream": item.get("source_stream"),
            "fallback_used": item.get("fallback_used", False),
        }
        existing = course_records.get(code)
        if existing is not None and existing["course"] != course:
            raise ValueError(f"Conflicting course data for contract code {code}")
        course_records[code] = {
            "course": course,
            "course_data": course_data,
            "source_hash": source_hash,
        }





def export_translated_ctdt(config_path: str = "config.yaml") -> tuple[int, list[dict]]:
    """Materialize translated CTDT records and extract mapping contracts."""
    config = read_yaml_config(config_path)
    materialize_ctdt_batch(config_path, translated_only=True)
    canonical_root = Path(config["paths"].get("canonical", "data/8_canonical")) / "ctdt"
    contract_root = Path(config["paths"].get("contract_export", "../../contract"))
    course_records: dict[str, dict[str, Any]] = {}
    count = 0

    for path in sorted(canonical_root.glob("CTDT_*.json")):
        program = read_json(path)
        if not isinstance(program, dict) or not program.get("ma_ctdt"):
            continue
        _write_program_contract(program, contract_root, course_records)
        count += 1

    formatted_courses = []
    for code, record in sorted(course_records.items()):
        course = record["course"]
        formatted_courses.append({
            "ma_hoc_phan": code,
            "hoc_phan": record["course_data"],
            "muc_tieu_hoc_phan": course.get("muc_tieu_hoc_phan", []),
            "clo": course.get("clo", []),
            "bai_hoc": course.get("bai_hoc", []),
        })

    return count, formatted_courses


if __name__ == "__main__":
    export_translated_ctdt()