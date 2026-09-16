"""M3 assembly: combine translated entities into canonical course records."""

from collections import defaultdict
from pathlib import Path
from typing import Any

from shared.file_io import get_content_hash, read_json, read_yaml_config, write_json
from shared.logger import get_logger

logger = get_logger("m3_assemble")


def _translated_files(input_root: Path) -> list[Path]:
    return sorted((input_root / "vi_en").rglob("*.json"))


def assemble_course(entities: list[dict[str, Any]]) -> dict[str, Any]:
    if not entities:
        raise ValueError("Cannot assemble an empty entity list")

    course_code = entities[0]["ma_hoc_phan"]
    canonical: dict[str, Any] = {
        "ma_hoc_phan": course_code,
        "crawl_course_key": f"COURSE_{course_code}",
        "hoc_phan": {},
        "muc_tieu_hoc_phan": [],
        "clo": [],
        "bai_hoc": [],
        "entity_ids": [],
        "source_hashes": [],
        "field_provenance": {},
        "translation_status": "translated",
    }

    for entity in entities:
        entity_type = entity["entity_type"]
        data_vi = entity.get("data_vi") or {}
        data_en = entity.get("data_en") or {}

        if isinstance(data_vi, list):
            data = []
            for vi_item, en_item in zip(data_vi, data_en):
                item = dict(vi_item)
                for field, value in en_item.items():
                    item[f"{field}_en"] = value
                data.append(item)
        else:
            data = dict(data_vi)
            for field, value in data_en.items():
                if entity_type == "hoc_phan" and field == "ten_vi":
                    if not data.get("ten_en"):
                        data["ten_en"] = value
                else:
                    data[f"{field}_en"] = value

        if entity_type == "hoc_phan":
            canonical["hoc_phan"].update(data)
        elif entity_type == "muc_tieu":
            canonical["muc_tieu_hoc_phan"].extend(data if isinstance(data, list) else [data])
        else:
            canonical[entity_type].extend(data if isinstance(data, list) else [data])

        canonical["entity_ids"].append(entity["entity_id"])
        if entity["source_hash"] not in canonical["source_hashes"]:
            canonical["source_hashes"].append(entity["source_hash"])
        canonical["field_provenance"].update({
            f"{entity['entity_id']}.{field}": value
            for field, value in entity.get("field_provenance", {}).items()
        })

    canonical["content_hash"] = get_content_hash(canonical)
    return canonical


def assemble_batch(config_path: str = "config.yaml") -> int:
    config = read_yaml_config(config_path)
    input_root = Path(config["paths"].get("translated_entities", "data/7_translated_entities"))
    output_root = Path(config["paths"].get("canonical", "data/8_canonical"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for path in _translated_files(input_root):
        entity = read_json(path)
        if isinstance(entity, dict) and entity.get("ma_hoc_phan"):
            grouped[entity["ma_hoc_phan"]].append(entity)

    count = 0
    for course_code, entities in grouped.items():
        target_dir = output_root / ("mhtml" if any(
            "hoc_phan_bo_sung" in entity.get("source_file", "") for entity in entities
        ) else "syllabus")
        target = target_dir / f"COURSE_{course_code}.json"
        if target.exists():
            continue
        write_json(target, assemble_course(entities))
        count += 1

    logger.info(f"M3 assembly complete: {count} canonical records")
    return count


if __name__ == "__main__":
    assemble_batch()
