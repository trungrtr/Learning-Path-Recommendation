"""CLI for extracting programme-level CTDT structure with an LLM."""

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
from pipeline.extract_ctdt.chuyen_doi import normalize_ctdt_payload, validate_ctdt_document
from pipeline.extract_ctdt.doc_reader import SUPPORTED_SUFFIXES, read_source_text
from pipeline.extract_ctdt.goi_llm import extract_ctdt_with_llm
from pipeline.extract_ctdt.table_parser import parse_ctdt_pdf_table


def _iter_input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files: list[Path] = []
    for suffix in sorted(SUPPORTED_SUFFIXES):
        files.extend(input_path.glob(f"*{suffix}"))
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract CTDT curriculum structure using LLM.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, help="Override CTDT input file or directory.")
    parser.add_argument("--output", type=Path, help="Override CTDT output directory.")
    parser.add_argument("--prompt", type=Path, help="Override CTDT extraction prompt.")
    args = parser.parse_args()

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    settings = load_settings(args.config)
    paths = settings["paths"]
    llm_settings = settings.get("ctdt_extraction_llm", {})
    prompts_dir = llm_settings.get("prompts_dir") or settings["extraction_llm"]["prompts_dir"]

    input_path = args.input or ROOT_DIR / paths.get("ctdt_input_dir", "data/00_input/CTDT")
    output_dir = args.output or ROOT_DIR / paths.get("ctdt_extracted_dir", "data/01_ctdt_extracted")
    prompt_path = args.prompt or ROOT_DIR / prompts_dir / "ctdt_extraction.txt"

    input_files = _iter_input_files(input_path)
    if not input_files:
        raise FileNotFoundError(f"No CTDT source files found in {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_template = prompt_path.read_text(encoding="utf-8")

    for source_path in input_files:
        logging.info("Extracting CTDT from %s", source_path.name)
        if source_path.suffix.casefold() == ".pdf":
            try:
                raw_payload = parse_ctdt_pdf_table(source_path)
            except Exception:
                logging.exception("Structured CTDT PDF parser failed; falling back to LLM extraction.")
                source_text = read_source_text(source_path)
                raw_payload = extract_ctdt_with_llm(source_text, prompt_template, llm_settings)
        else:
            source_text = read_source_text(source_path)
            raw_payload = extract_ctdt_with_llm(source_text, prompt_template, llm_settings)
        document = normalize_ctdt_payload(raw_payload)
        validate_ctdt_document(document)
        output_path = output_dir / f"{source_path.stem}.json"
        output_path.write_text(
            document.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )
        logging.info("Wrote %s", output_path)


if __name__ == "__main__":
    main()
