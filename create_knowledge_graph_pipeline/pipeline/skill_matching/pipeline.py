"""Orchestrate closed-pool retrieval through validated course-skill output."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from .aggregate import aggregate_by_course
from .candidate_retrieval import CandidateRetriever
from .config import DEFAULT_CONFIG, SkillMatchingConfig, load_skill_matching_config
from .consolidation import consolidate_candidates
from .evidence_validator import EvidenceValidator, ValidationBackend
from .models import CourseSkillResult
from .query_builder import build_match_queries
from .reranker import UniSkillReranker
from .skill_pool import build_skill_pool

LOGGER = logging.getLogger(__name__)
EXPERIMENTAL_LIMITATIONS = [
    "Thresholds are not calibrated against a human-reviewed Gold Dataset.",
    "UniSkill_BERT remains experimental until a reviewed IT-30 checkpoint is available.",
]


def _input_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".json" else []
    if input_path.is_dir():
        return sorted(input_path.glob("*.json"))
    return []


def _load_units(path: Path) -> list[dict[str, Any]] | None:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        LOGGER.warning("Skipping invalid translated-unit JSON %s: %s", path, exc)
        return None
    if not isinstance(payload, list) or not all(isinstance(unit, dict) for unit in payload):
        LOGGER.warning("Skipping %s because translated-unit output must be a list.", path)
        return None
    return payload


def _course_metadata(units: list[dict[str, Any]], fallback: str) -> dict[str, dict[str, str | None]]:
    course_id = next(
        (unit.get("course_id") for unit in units if isinstance(unit.get("course_id"), str)),
        fallback,
    )
    first = next((unit for unit in units if unit.get("course_id") == course_id), {})
    return {
        course_id: {
            "course_code": first.get("course_code"),
            "internal_course_code": first.get("internal_course_code"),
        }
    }


def _write_course_result(result: dict[str, Any], source_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    validated = CourseSkillResult.model_validate(result)
    (output_dir / source_path.name).write_text(
        validated.model_dump_json(indent=2, exclude_none=True),
        encoding="utf-8",
    )


def run_skill_matching(
    config: SkillMatchingConfig,
    input_path: Path | None = None,
    output_dir: Path | None = None,
    *,
    validation_backend: ValidationBackend | None = None,
) -> tuple[int, int, int]:
    """Run query → retrieval → scoring → consolidation → validation → aggregation."""
    source = input_path or config.input_dir
    destination = output_dir or config.output_dir
    pool = build_skill_pool(config)
    retriever = CandidateRetriever(config)
    reranker = UniSkillReranker(config)
    validator = EvidenceValidator(config, validation_backend)
    course_count = candidate_count = match_count = 0

    for source_path in _input_files(source):
        units = _load_units(source_path)
        if units is None:
            continue
        metadata = _course_metadata(units, source_path.stem)
        course_id = next(iter(metadata))
        queries = build_match_queries(units, course_id, pool, config)
        candidates = retriever.retrieve(queries, pool)
        scored = reranker.rerank(candidates)
        consolidated = consolidate_candidates(
            scored,
            max_evidence=config.max_validation_evidence,
            top_n_per_course=config.validator_top_n_per_course,
        )
        validated = validator.validate(consolidated)
        results = aggregate_by_course(
            validated,
            course_metadata=metadata,
            calibration_status=config.output_calibration_status,
            limitations=EXPERIMENTAL_LIMITATIONS,
            max_skills_per_course=config.max_skills_per_course,
        )
        result = results[0]
        _write_course_result(result, source_path, destination)

        course_count += 1
        candidate_count += len(candidates)
        file_match_count = len(result["matched_skills"])
        match_count += file_match_count
        LOGGER.info(
            "Matched %s: %d queries -> %d candidates -> %d consolidated -> %d validated skills",
            source_path.name,
            len(queries),
            len(candidates),
            len(consolidated),
            file_match_count,
        )
    return course_count, candidate_count, match_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Match translated course units to closed-pool ESCO skills.")
    parser.add_argument("input", nargs="?", type=Path, help="One translated-unit JSON or its directory.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, help="Directory containing one result per course.")
    args = parser.parse_args()
    config = load_skill_matching_config(args.config)
    courses, candidates, matches = run_skill_matching(config, args.input, args.output)
    print(f"Processed courses: {courses}")
    print(f"Retrieved candidates: {candidates}")
    print(f"Validated ESCO skills: {matches}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
