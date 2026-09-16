"""Materialize course data grouped by training programme (CTDT)."""

from collections import defaultdict
from pathlib import Path
from typing import Any

from shared.file_io import get_content_hash, read_json, read_yaml_config, write_json
from shared.logger import get_logger

logger = get_logger("m3_materialize_ctdt")

SOURCE_STREAMS = ("hoc_phan", "hoc_phan_bo_sung")
ENTITY_KEYS = {
    "hoc_phan": "hoc_phan",
    "muc_tieu": "muc_tieu_hoc_phan",
    "clo": "clo",
    "bai_hoc": "bai_hoc",
}


def _merge_translated_entities(entities: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one course record without changing the existing assembler."""
    if not entities:
        raise ValueError("Cannot materialize an empty entity list")

    course_code = entities[0]["ma_hoc_phan"]
    course: dict[str, Any] = {
        "ma_hoc_phan": course_code,
        "crawl_course_key": f"COURSE_{course_code}",
        "hoc_phan": {},
        "muc_tieu_hoc_phan": [],
        "clo": [],
        "bai_hoc": [],
        "entity_ids": [],
        "source_hashes": [],
        "translation_status": "translated",
    }

    for entity in entities:
        entity_type = entity.get("entity_type")
        target_key = ENTITY_KEYS.get(entity_type)
        if not target_key:
            continue

        data_vi = entity.get("data_vi") or entity.get("data") or {}
        data_en = entity.get("data_en") or {}
        if isinstance(data_vi, list):
            data = []
            en_list = data_en if isinstance(data_en, list) else []
            for i, vi_item in enumerate(data_vi):
                item = dict(vi_item)
                if i < len(en_list):
                    for field, value in en_list[i].items():
                        item[f"{field}_en"] = value
                data.append(item)
        else:
            data = dict(data_vi)
            if isinstance(data_en, dict):
                for field, value in data_en.items():
                    data[f"{field}_en"] = value

        if target_key == "hoc_phan":
            course[target_key].update(data)
        else:
            course[target_key].extend(data if isinstance(data, list) else [data])

        if entity.get("entity_id"):
            course["entity_ids"].append(entity["entity_id"])
        if entity.get("source_hash") and entity["source_hash"] not in course["source_hashes"]:
            course["source_hashes"].append(entity["source_hash"])

    course["content_hash"] = get_content_hash(course)
    return course


def _load_course_index(translated_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    index: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
        stream: defaultdict(dict) for stream in SOURCE_STREAMS
    }
    normalized_root = translated_root.parent / "normalized_entities"
    for stream in SOURCE_STREAMS:
        # Load normalized data first; translated entities replace it per type
        # when available, so materialization also works before LLM translation.
        for root in (normalized_root / stream, translated_root / "vi_en" / stream):
            for path in sorted(root.glob("**/*.json")):
                entity = read_json(path)
                if not isinstance(entity, dict) or not entity.get("ma_hoc_phan") or not entity.get("entity_type"):
                    continue
                index[stream][entity["ma_hoc_phan"]][entity["entity_type"]] = entity

    return {
        stream: {
            code: _merge_translated_entities(list(entities.values()))
            for code, entities in courses.items()
        }
        for stream, courses in index.items()
    }


def _ctdt_courses(record: dict[str, Any]) -> list[dict[str, Any]]:
    data = record.get("data", {})
    if not isinstance(data, dict):
        return []
    if isinstance(data.get("hoc_phan_flat"), list):
        return data["hoc_phan_flat"]
    return [
        {
            "ma_hoc_phan": course.get("ma_hoc_phan"),
            "ten_hoc_phan": course.get("ten_hoc_phan"),
            "nhom_id": group.get("ten_nhom"),
            "loai_nhom": group.get("loai_nhom"),
        }
        for group in data.get("nhom_hoc_phan", [])
        for course in group.get("hoc_phan", [])
    ]


def materialize_ctdt(
    ctdt_record: dict[str, Any],
    course_index: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    data = ctdt_record.get("data", {})
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    program_code = str(ctdt_record.get("ma_ctdt") or meta.get("ma_ctdt") or "").strip()
    memberships: dict[str, dict[str, Any]] = {}

    for membership in _ctdt_courses(ctdt_record):
        course_code = str(membership.get("ma_hoc_phan") or "").strip()
        if not course_code:
            continue
        item = memberships.setdefault(
            course_code,
            {"ma_hoc_phan": course_code, "memberships": [], "course": None},
        )
        item["memberships"].append({key: membership.get(key) for key in membership})

    unresolved: list[str] = []
    for course_code, item in memberships.items():
        if course_code in course_index["hoc_phan"]:
            item.update({
                "course": course_index["hoc_phan"][course_code],
                "source_stream": "hoc_phan",
                "fallback_used": False,
                "resolution_status": "resolved",
            })
        elif course_code in course_index["hoc_phan_bo_sung"]:
            item.update({
                "course": course_index["hoc_phan_bo_sung"][course_code],
                "source_stream": "hoc_phan_bo_sung",
                "fallback_used": True,
                "resolution_status": "resolved_by_fallback",
            })
        else:
            item.update({
                "source_stream": None,
                "fallback_used": False,
                "resolution_status": "unresolved",
            })
            unresolved.append(course_code)

    output = {
        "ma_ctdt": program_code,
        "crawl_course_key": f"CTDT_{program_code}",
        "program": meta,
        "courses": list(memberships.values()),
        "unresolved_course_codes": unresolved,
        "resolution_summary": {
            "course_count": len(memberships),
            "resolved_count": len(memberships) - len(unresolved),
            "fallback_count": sum(item.get("fallback_used", False) for item in memberships.values()),
            "unresolved_count": len(unresolved),
        },
        "source_ctdt_entity_id": ctdt_record.get("entity_id"),
    }
    output["content_hash"] = get_content_hash(output)
    return output


def materialize_ctdt_batch(
    config_path: str = "config.yaml",
    translated_only: bool = False,
) -> int:
    config = read_yaml_config(config_path)
    translated_root = Path(config["paths"].get("translated_entities", "data/translated_entities"))
    output_root = Path(config["paths"].get("canonical", "data/8_canonical")) / "ctdt"
    ctdt_root = translated_root / "ctdt"
    if not ctdt_root.is_dir():
        if translated_only:
            logger.warning("No translated CTDT directory found in %s", translated_root)
            return 0
        ctdt_root = translated_root.parent / "normalized_entities" / "ctdt"
    course_index = _load_course_index(translated_root)
    count = 0

    for path in sorted(ctdt_root.glob("*.json")):
        record = read_json(path)
        if not isinstance(record, dict):
            continue
        materialized = materialize_ctdt(record, course_index)
        program_code = materialized["ma_ctdt"]
        if not program_code:
            logger.warning("Skip CTDT without ma_ctdt: %s", path)
            continue
        write_json(output_root / f"CTDT_{program_code}.json", materialized)
        count += 1

    logger.info("CTDT materialization complete: %d program(s)", count)
    return count


if __name__ == "__main__":
    materialize_ctdt_batch()