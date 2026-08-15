"""CLI for Stage 1: course Markdown syllabi to schema-valid Layer 1 JSON."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.extract_course.cau_hinh import (
    DEFAULT_CONFIG,
    ROOT_DIR,
    extraction_settings,
    extraction_validation_settings,
    infer_course_key,
    load_course_keys,
    load_settings,
)
from pipeline.extract_course.chuyen_doi import build_document
from pipeline.extract_course.goi_langextract import extract_from_markdown
from pipeline.extract_course.noise_rules import apply_lightweight_noise_rules


def main() -> None:
    """Extract every Markdown file and write one strict Layer 1 JSON per source."""
    parser = argparse.ArgumentParser(description="Extract course Markdown syllabi with LangExtract.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, help="Override markdown_input_dir from config.")
    parser.add_argument("--output", type=Path, help="Override extracted_dir from config.")
    parser.add_argument("--reports", type=Path, help="Override extraction rejection report directory.")
    parser.add_argument(
        "--course-key-map",
        type=Path,
        help="Optional JSON map: filename.md -> crawl_course_key.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    settings = load_settings(args.config)
    llm_settings = extraction_settings(settings)
    validation_settings = extraction_validation_settings(settings)
    input_dir = args.input or ROOT_DIR / settings["paths"]["markdown_input_dir"]
    output_dir = args.output or ROOT_DIR / settings["paths"]["extracted_dir"]
    reports_dir = args.reports or ROOT_DIR / settings["paths"]["extraction_rejection_reports_dir"]
    prompt_path = ROOT_DIR / llm_settings["prompts_dir"] / "extraction.txt"
    course_keys = load_course_keys(args.course_key_map)

    markdown_files = sorted(input_dir.glob("*.md"))
    if not markdown_files:
        raise FileNotFoundError(f"No Markdown files found in {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text(encoding="utf-8")

    for markdown_path in markdown_files:
        course_key = infer_course_key(markdown_path, course_keys)
        output_path = output_dir / f"{course_key}_{markdown_path.stem}.json"
        if output_path.exists():
            logging.info("Skipping %s, already extracted.", markdown_path.name)
            continue

        logging.info("Extracting %s", markdown_path.name)
        extractions = extract_from_markdown(
            markdown_path.read_text(encoding="utf-8"),
            prompt,
            llm_settings,
        )
        document = build_document(
            markdown_path,
            extractions,
            course_key,
            llm_settings["extractor_model"],
        )
        document, rejection_report = apply_lightweight_noise_rules(
            document,
            enabled=validation_settings["enabled"],
            report_ambiguous=validation_settings["report_ambiguous"],
        )
        output_path = output_dir / f"{course_key}_{markdown_path.stem}.json"
        output_path.write_text(
            document.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{course_key}_{markdown_path.stem}.rejections.json"
        report_path.write_text(
            rejection_report.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logging.info("Wrote %s", output_path)
        if rejection_report.items:
            logging.info("Wrote %d extraction validation items to %s", len(rejection_report.items), report_path)


if __name__ == "__main__":
    main()
