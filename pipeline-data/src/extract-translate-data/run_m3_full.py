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
    logger.info("=== START FULL M3 PIPELINE ===")

    logger.info("1. Normalizing (Syllabus & CTDT)...")
    from pipeline.m3.normalize import normalize_batch
    normalize_batch()

    logger.info("1.5. Enriching General Courses (LLM + History)...")
    from pipeline.m3.enrich_general_courses import enrich_batch
    enrich_batch()

    logger.info("2. Translating Syllabus...")
    from pipeline.m3.translate import translate_batch
    translate_batch()

    logger.info("3. Translating CTDT...")
    from pipeline.m3.translate_ctdt import translate_ctdt_batch
    translate_ctdt_batch()

    logger.info("4. Assembling Syllabus L1 -> L2...")
    from pipeline.m3.assemble import assemble_batch
    assemble_batch()

    logger.info("5. Materializing CTDT...")
    from pipeline.m3.materialize_ctdt import materialize_ctdt_batch
    materialize_ctdt_batch()

    logger.info("6. Exporting CTDT to Contract...")
    from pipeline.m3.export_ctdt_translated import export_translated_ctdt
    count, ctdt_courses = export_translated_ctdt()
    
    logger.info("7. Exporting Syllabus to Contract (CTDT courses only)...")
    from pipeline.m3.export_for_skill_mapping import export_batch
    export_batch(ctdt_courses)

    logger.info("=== DONE M3 FULL PIPELINE ===")
except Exception as e:
    logger.exception(f"Pipeline crashed: {e}")
