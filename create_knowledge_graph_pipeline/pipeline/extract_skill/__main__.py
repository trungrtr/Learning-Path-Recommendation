"""CLI cho tiến trình trích xuất keyword skill từ đề cương (Layer 2 -> Layer 3)."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG, ROOT_DIR, load_settings
from pipeline.extract_skill.chuyen_doi import enrich_document_with_skills
from pipeline.extract_skill.goi_llm import extract_skills_with_llm


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract keyword skills using LLM.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, help="Override input dir.")
    parser.add_argument("--output", type=Path, help="Override output dir.")
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    
    settings = load_settings(args.config)
    
    input_dir = args.input or ROOT_DIR / settings["paths"]["canonical_dir"]
    output_dir = args.output or ROOT_DIR / "data" / "03_skill_keywords"
    
    input_files = sorted(input_dir.glob("*.json"))
    if not input_files:
        logging.error(f"No JSON files found in {input_dir}")
        return
        
    output_dir.mkdir(parents=True, exist_ok=True)

    for json_path in input_files:
        logging.info("Trích xuất skill cho: %s", json_path.name)
        try:
            course_data = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Bỏ qua file không hợp lệ %s: %s", json_path, exc)
            continue
            
        raw_skills = extract_skills_with_llm(course_data)
        
        layer3_doc = enrich_document_with_skills(course_data, raw_skills)
        
        output_path = output_dir / json_path.name
        output_path.write_text(
            layer3_doc.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        logging.info("Đã lưu %s", output_path)

if __name__ == "__main__":
    main()
