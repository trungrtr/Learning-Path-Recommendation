import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
sys.path.insert(0, os.path.abspath('.'))
from shared.logger import get_logger
from shared.file_io import read_json
logger = get_logger("run_m3_full")

try:
    logger.info("=== START M3 ASSEMBLE & EXPORT FIX ===")

    logger.info("4. Assembling Syllabus L1 -> L2...")
    from pipeline.m3.assemble import assemble_batch
    assemble_batch()

    logger.info("5. Materializing CTDT...")
    from pipeline.m3.materialize_ctdt import materialize_ctdt_batch
    materialize_ctdt_batch()

    logger.info("6. Exporting Syllabus to Contract...")
    from pipeline.m3.export_for_skill_mapping import export_batch
    
    courses = []
    for path in Path("data/8_canonical").rglob("*.json"):
        if "ctdt" not in str(path):
            try:
                courses.append(read_json(path))
            except Exception:
                pass
    export_batch(courses)

    logger.info("7. Exporting CTDT to Contract...")
    from pipeline.m3.export_ctdt_translated import export_translated_ctdt
    export_translated_ctdt()

    logger.info("=== DONE M3 FULL PIPELINE ===")
except Exception as e:
    logger.exception(f"Pipeline crashed: {e}")
