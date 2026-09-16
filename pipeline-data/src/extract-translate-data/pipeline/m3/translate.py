"""M3 translation: translate entity fields for hoc phan and hoc phan bo sung.

Input:   data/normalized_entities/{hoc_phan,hoc_phan_bo_sung}/**/*.json
Output:  data/translated_entities/
           vi_en/{hoc_phan,hoc_phan_bo_sung}/**/*.json  -- bilingual (VI + EN)
           en/{hoc_phan,hoc_phan_bo_sung}/**/*.json     -- English only

Output schema
vi_en/: entity_id, entity_type, ma_hoc_phan, source_hash,
        translation_model, translation_status, data_vi, data_en
en/:    entity_id, entity_type, ma_hoc_phan, source_hash, data

Excluded from output: translation_input_hash, field_provenance, source_file.
CTDT entities are handled by translate_ctdt.py -- excluded here.
"""

import json
from pathlib import Path
from typing import Any

from shared.file_io import read_json, read_yaml_config, write_json
from shared.logger import get_logger

logger = get_logger("m3_translate")

TRANSLATABLE_FIELDS: dict[str, tuple[str, ...]] = {
    "hoc_phan": ("ten_vi", "mo_ta_tom_tat"),
    "muc_tieu": ("noi_dung",),
    "clo":      ("noi_dung",),
    "bai_hoc":  ("ten_bai", "noi_dung_tom_tat"),
}

ENTITY_SOURCE_DIRS: tuple[str, ...] = ("hoc_phan", "hoc_phan_bo_sung")

_BASE_INSTRUCTION = (
    "Translate the following Vietnamese educational fields to precise English. "
    "Use standard academic / CS terminology where an established term exists "
    "(e.g. 'Data Structures and Algorithms', 'Probability and Statistics', "
    "'Marxist-Leninist Philosophy', 'Ho Chi Minh Thought'). "
    "Preserve null values, codes, numbers, and technical names. "
    "Do not add fields, explanations, or markdown code fences. "
)


def _translation_prompt(entity: dict[str, Any]) -> str:
    fields = TRANSLATABLE_FIELDS.get(entity["entity_type"], ())
    data = entity.get("data", {})
    if isinstance(data, list):
        values = [{f: item.get(f) for f in fields} for item in data]
        return (
            _BASE_INSTRUCTION
            + f"Return a JSON ARRAY with exactly {len(values)} objects, same field names.\n"
            + json.dumps(values, ensure_ascii=False)
        )
    else:
        values = {f: data.get(f) for f in fields}
        return (
            _BASE_INSTRUCTION
            + "Return a JSON OBJECT with exactly the same field names.\n"
            + json.dumps(values, ensure_ascii=False)
        )


def _parse_response(raw: str, expect_list: bool) -> dict | list:
    """Strip markdown fences, parse JSON, coerce shape. Returns empty on failure."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.rsplit("```", 1)[0].strip()
    if not raw:
        return [] if expect_list else {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return [] if expect_list else {}
    if expect_list:
        return parsed if isinstance(parsed, list) else ([parsed] if isinstance(parsed, dict) else [])
    else:
        return parsed if isinstance(parsed, dict) else {}


def translate_entity(entity: dict[str, Any], model: str) -> tuple[dict, dict]:
    """Translate one entity. Returns (vi_en_envelope, en_only_envelope)."""
    from shared.llm_client import call_gemini

    fields = TRANSLATABLE_FIELDS.get(entity["entity_type"], ())
    data = entity.get("data", {})
    is_list = isinstance(data, list)

    if is_list:
        payload = [{f: item.get(f) for f in fields if item.get(f) is not None} for item in data]
        has_content = any(p for p in payload)
    else:
        payload = {f: data.get(f) for f in fields if data.get(f) is not None}
        has_content = bool(payload)

    if has_content:
        raw = call_gemini(_translation_prompt(entity), model)
        data_en = _parse_response(raw, expect_list=is_list)
    else:
        data_en = [] if is_list else {}

    vi_en = {
        "entity_id":          entity["entity_id"],
        "entity_type":        entity["entity_type"],
        "ma_hoc_phan":        entity.get("ma_hoc_phan"),
        "source_hash":        entity["source_hash"],
        "translation_model":  model,
        "translation_status": "translated",
        "data_vi":            entity.get("data", {}),
        "data_en":            data_en,
    }

    en_only = {
        "entity_id":   entity["entity_id"],
        "entity_type": entity["entity_type"],
        "ma_hoc_phan": entity.get("ma_hoc_phan"),
        "source_hash": entity["source_hash"],
        "data":        data_en,
    }

    return vi_en, en_only


def translate_batch(config_path: str = "config.yaml") -> int:
    """Translate all hoc phan / hoc phan bo sung entities.

    Output:
        data/translated_entities/
            vi_en/hoc_phan/...          bilingual
            vi_en/hoc_phan_bo_sung/...
            en/hoc_phan/...             English only
            en/hoc_phan_bo_sung/...

    Idempotent: skips files already present in vi_en/ output.
    """
    config      = read_yaml_config(config_path)
    norm_root   = Path(config["paths"].get("normalized",          "data/normalized_entities"))
    out_root    = Path(config["paths"].get("translated_entities", "data/translated_entities"))
    model       = config["models"]["gemini_translation"]
    vi_en_root  = out_root / "vi_en"
    en_root     = out_root / "en"
    count       = 0

    for src_dir_name in ENTITY_SOURCE_DIRS:
        src_dir = norm_root / src_dir_name
        if not src_dir.is_dir():
            logger.warning("Source directory not found, skipping: %s", src_dir)
            continue

        for src_path in sorted(src_dir.glob("**/*.json")):
            entity = read_json(src_path)
            if not isinstance(entity, dict) or "entity_id" not in entity:
                continue
            if entity.get("entity_type") not in TRANSLATABLE_FIELDS:
                continue

            relative  = src_path.relative_to(norm_root)
            vi_en_out = vi_en_root / relative
            en_out    = en_root    / relative

            if vi_en_out.exists():
                try:
                    existing = read_json(vi_en_out)
                    if isinstance(existing, dict) and existing.get("data_vi") == entity.get("data"):
                        logger.debug("Already translated and data matches, skipping: %s", src_path.name)
                        continue
                except Exception:
                    pass

            try:
                vi_en, en_only = translate_entity(entity, model)
                write_json(vi_en_out, vi_en)
                write_json(en_out, en_only)
                count += 1
                logger.info("Translated -> %s", relative)
            except NotImplementedError:
                logger.warning("call_gemini not implemented, stopping.")
                break
            except Exception as exc:
                logger.error("Failed %s: %s", src_path.name, exc)

    logger.info("M3 translation complete: %d file(s) written.", count)
    return count


if __name__ == "__main__":
    translate_batch()
