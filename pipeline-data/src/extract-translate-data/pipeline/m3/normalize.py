"""M3 normalization: clean and group entities by source stream and course."""

import re
import unicodedata
from pathlib import Path
from typing import Any

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from shared.file_io import get_content_hash, read_json, read_yaml_config, write_json
from shared.logger import get_logger
from pipeline.m3.normalize_ctdt import process_ctdt_record

logger = get_logger("m3_normalize")

ENTITY_TYPES = ("tom_tat_hp", "muc_tieu", "clo", "bai_hoc")
SOURCE_STREAMS = ("ctdt", "hoc_phan", "hoc_phan_bo_sung")


def _source_hash(record: dict[str, Any]) -> str:
    return str(record.get("content_hash") or get_content_hash(record))


def _entity_id(course_code: str, entity_type: str) -> str:
    return f"{course_code}:{entity_type}"


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip().lower() not in {"null", "none", "n/a", "-"}]


def _normalize_name(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip().casefold()
    return text


def _clean_lessons(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the first lesson/chapter with each normalized name."""
    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []
    for item in items:
        name = str(item.get("ten_bai") or "").strip()
        key = _normalize_name(name)
        if not key or key in seen:
            continue
        seen.add(key)
        cleaned.append({
            "ten_bai": name,
            "noi_dung_tom_tat": item.get("noi_dung_tom_tat"),
            "ma_clo": _clean_list(item.get("ma_clo")),
        })
    return cleaned


def normalize_record(record: dict[str, Any], source_file: str) -> list[dict[str, Any]]:
    """Return one normalized file payload per entity type, without changing input."""
    course_code = str(record.get("ma_hoc_phan") or "UNKNOWN")
    filename_match = re.match(r"([A-Za-z]{2}\d{4})(?:_|\.)", Path(source_file).name)
    filename_code = filename_match.group(1).upper() if filename_match else None
    source_code = str(record.get("source_course_code") or "").strip().upper()
    if filename_code and course_code.upper() != filename_code:
        logger.error(
            "Reject filename/content mismatch: %s declares %s, filename declares %s",
            source_file,
            course_code,
            filename_code,
        )
        return []
    if source_code and course_code.upper() != source_code:
        logger.error(
            "Reject course identifier mismatch: %s declares %s, source declares %s",
            source_file,
            course_code,
            source_code,
        )
        return []
    if not re.fullmatch(r"[A-Z]{2}\d{4}", course_code.upper()):
        logger.error("Reject invalid course identifier %r from %s", course_code, source_file)
        return []
    source_hash = _source_hash(record)
    entities: list[dict[str, Any]] = []

    course = record.get("hoc_phan")
    if isinstance(course, dict):
        entities.append(_build_entity(course_code, "hoc_phan", course, source_file, source_hash))

    for entity_type in ENTITY_TYPES[1:]:
        items = record.get(entity_type if entity_type != "muc_tieu" else "muc_tieu_hoc_phan")
        if not isinstance(items, list):
            continue
        items = [item for item in items if isinstance(item, dict)]
        if entity_type == "bai_hoc":
            items = _clean_lessons(items)
        if items:
            entities.append(_build_entity(course_code, entity_type, items, source_file, source_hash))
    return entities


def _build_entity(
    course_code: str,
    entity_type: str,
    data: dict[str, Any] | list[dict[str, Any]],
    source_file: str,
    source_hash: str,
) -> dict[str, Any]:
    sample = data if isinstance(data, dict) else (data[0] if data else {})
    fields = sample.keys()
    return {
        "entity_id": _entity_id(course_code, entity_type),
        "entity_type": entity_type,
        "ma_hoc_phan": course_code,
        "source_file": source_file,
        "source_hash": source_hash,
        "field_provenance": {field: "extracted" for field in fields},
        "review_status": "not_required",
        "data": data,
    }


def _normalize_ctdt_record(record: dict[str, Any], source_file: str) -> dict[str, Any] | None:
    # Lấy ma_ctdt từ object gốc hoặc từ field 'data'
    program_code = str(record.get("data", {}).get("ma_ctdt") or record.get("ma_ctdt") or "").strip()
    if not program_code:
        return None
        
    normalized_data = process_ctdt_record(record, source_file)
    
    return {
        "entity_id": f"{program_code}:ctdt",
        "entity_type": "ctdt",
        "ma_ctdt": program_code,
        "source_file": source_file,
        "source_hash": _source_hash(record),
        "field_provenance": {field: "extracted" for field in record},
        "review_status": "not_required",
        "data": normalized_data,
    }


def _input_files(config: dict[str, Any]) -> tuple[list[Path], list[Path]]:
    root = Path(config["paths"]["extracted"])
    files = list((root / "hoc_phan").glob("*.json"))
    files.extend((root / "hoc_phan_bo_sung").glob("*.json"))
    return sorted(set(files)), sorted((root / "ctdt").glob("*.json"))


def _source_stream(source_path: Path) -> str:
    if source_path.parent.name == "hoc_phan_bo_sung":
        return "hoc_phan_bo_sung"
    return "hoc_phan"


def _remove_source_entities(output_root: Path, source_file: str) -> None:
    """Remove prior entities produced from the same source before rebuilding."""
    for path in output_root.glob("hoc_phan*/**/*.json"):
        try:
            payload = read_json(path)
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict) and payload.get("source_file") == source_file:
            path.unlink()


def normalize_batch(config_path: str = "config.yaml") -> int:
    config = read_yaml_config(config_path)
    output_root = Path(config["paths"].get("normalized", "data/normalized_entities"))
    count = 0
    course_files, ctdt_files = _input_files(config)
    for source_path in course_files:
        _remove_source_entities(output_root, source_path.name)
        record = read_json(source_path)
        if not isinstance(record, dict):
            logger.warning(f"Skip non-object source: {source_path}")
            continue
        for entity in normalize_record(record, source_path.name):
            entity_path = (
                output_root
                / _source_stream(source_path)
                / entity["entity_type"]
                / f"{entity['ma_hoc_phan']}__{entity['entity_type']}.json"
            )
            write_json(entity_path, entity)
            count += 1

    for source_path in ctdt_files:
        record = read_json(source_path)
        if not isinstance(record, dict):
            logger.warning(f"Skip non-object CTDT source: {source_path}")
            continue
        entity = _normalize_ctdt_record(record, source_path.name)
        if entity is None:
            logger.warning(f"Skip CTDT without ma_ctdt: {source_path}")
            continue
        entity_path = output_root / "ctdt" / f"{entity['ma_ctdt']}__ctdt.json"
        write_json(entity_path, entity)
        count += 1
    logger.info(f"M3 normalize complete: {count} entities")
    return count


if __name__ == "__main__":
    normalize_batch()
