"""Enrich missing CLO and Objectives for general/social courses."""

import os
import json
import logging
from pathlib import Path
from typing import Any

from shared.file_io import read_json, write_json, read_yaml_config
from shared.llm_client import call_gemini

logger = logging.getLogger("m3_enrich")


def load_history(history_dir: Path) -> dict[str, dict]:
    db = {}
    if not history_dir.exists():
        return db
    for p in history_dir.glob("*.json"):
        try:
            data = read_json(p)
            name_vi = data.get("course", {}).get("name_vi", "").strip()
            if name_vi:
                db[name_vi] = data
        except Exception as e:
            logger.warning(f"Failed to read history {p}: {e}")
    return db

def _generate_missing(ten_vi: str, mo_ta: str, bai_hoc: list, model: str) -> tuple[list, list]:
    prompt = f"""Dựa vào tên môn học '{ten_vi}', mô tả '{mo_ta}' và danh sách bài học sau, hãy suy luận và sinh ra 1-2 mục tiêu chung (muc_tieu) và 4-6 chuẩn đầu ra (CLO) bằng tiếng Việt.
Danh sách bài học:
{json.dumps(bai_hoc, ensure_ascii=False)}

Hãy trả về DUY NHẤT một cục JSON đúng chuẩn như sau, không giải thích gì thêm, không bọc markdown fences:
{{
  "muc_tieu": [
    {{"ma_muc_tieu": "G1", "loai_muc_tieu": "KIEN_THUC", "noi_dung": "...", "so_ctdt": []}}
  ],
  "clo": [
    {{"ma_clo": "CLO1", "noi_dung": "...", "chuan_da_ra_ctdt": [], "muc_tieu_hoc_phan": []}}
  ]
}}
"""
    raw = call_gemini(prompt, model)
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        parsed = json.loads(raw)
        return parsed.get("muc_tieu", []), parsed.get("clo", [])
    except Exception as e:
        logger.error(f"Failed to parse LLM response for {ten_vi}: {e}\n{raw}")
        return [], []

def _generate_muc_tieu_only(ten_vi: str, clos: list, model: str) -> list:
    prompt = f"""Dựa vào tên môn học '{ten_vi}' và danh sách chuẩn đầu ra CLO sau, hãy sinh ra 1-2 mục tiêu chung (muc_tieu) bằng tiếng Việt.
Danh sách CLO:
{json.dumps(clos, ensure_ascii=False)}

Hãy trả về DUY NHẤT một mảng JSON đúng chuẩn như sau, không giải thích gì thêm, không bọc markdown fences:
[
  {{"ma_muc_tieu": "G1", "loai_muc_tieu": "KIEN_THUC", "noi_dung": "...", "so_ctdt": []}}
]
"""
    raw = call_gemini(prompt, model)
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception as e:
        logger.error(f"Failed to parse LLM response for {ten_vi}: {e}")
        return []

def enrich_batch(config_path: str = "config.yaml"):
    config = read_yaml_config(config_path)
    model = config["models"]["gemini_translation"]
    norm_root = Path(config["paths"].get("normalized", "data/normalized_entities"))
    history_dir = Path("../../data/raw/data_his")
    
    if not history_dir.exists():
        logger.warning("No historical data found.")
    
    history_db = load_history(history_dir)
    logger.info(f"Loaded {len(history_db)} historical courses.")
    
    hp_dir = norm_root / "hoc_phan_bo_sung" / "hoc_phan"
    if not hp_dir.exists():
        return
        
    count = 0
    for p in sorted(hp_dir.glob("*.json")):
        code = p.stem.split("__")[0]
        
        data = read_json(p)
        ten_vi = data.get("data", {}).get("ten_vi", "")
        if not ten_vi:
            continue
            
        clo_path = norm_root / "hoc_phan_bo_sung" / "clo" / f"{code}__clo.json"
        mt_path = norm_root / "hoc_phan_bo_sung" / "muc_tieu" / f"{code}__muc_tieu.json"
        
        bh_path = norm_root / "hoc_phan_bo_sung" / "bai_hoc" / f"{code}__bai_hoc.json"
        bh_data = read_json(bh_path).get("data", []) if bh_path.exists() else []
        bh_titles = [b.get("ten_bai", "") for b in bh_data]
        
        clo_existing = read_json(clo_path) if clo_path.exists() else {}
        
        if not clo_existing.get("data"):
            logger.info(f"Enriching CLO and Muc Tieu for {code} - {ten_vi}...")
            if ten_vi in history_db:
                logger.info(f"-> MATCH FOUND in history for {ten_vi}!")
                his_clos = history_db[ten_vi].get("clos", [])
                
                transformed_clos = []
                for i, c in enumerate(his_clos):
                    transformed_clos.append({
                        "ma_clo": c.get("clo_code", f"CLO{i+1}"),
                        "noi_dung": c.get("content", ""),
                        "chuan_da_ra_ctdt": [],
                        "muc_tieu_hoc_phan": []
                    })
                    
                muc_tieus = _generate_muc_tieu_only(ten_vi, transformed_clos, model)
                final_clos = transformed_clos
            else:
                logger.info(f"-> NO MATCH in history. LLM generating from scratch...")
                muc_tieus, final_clos = _generate_missing(ten_vi, data.get("data", {}).get("mo_ta_tom_tat", ""), bh_titles, model)
            
            clo_entity = {
                "entity_id": f"{code}:clo",
                "entity_type": "clo",
                "ma_hoc_phan": code,
                "source_file": data.get("source_file"),
                "source_hash": data.get("source_hash"),
                "data": final_clos
            }
            clo_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(clo_path, clo_entity)
            
            mt_entity = {
                "entity_id": f"{code}:muc_tieu",
                "entity_type": "muc_tieu",
                "ma_hoc_phan": code,
                "source_file": data.get("source_file"),
                "source_hash": data.get("source_hash"),
                "data": muc_tieus
            }
            mt_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(mt_path, mt_entity)
            
            count += 1
            
    logger.info(f"Enriched {count} courses.")

if __name__ == "__main__":
    enrich_batch()
