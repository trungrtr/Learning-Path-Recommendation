"""Fail-fast command orchestrator for the complete HaUI KG pipeline."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG

LOGGER = logging.getLogger(__name__)
STAGES = ("extract_course", "merge", "extract_skill", "translate", "skill_matching", "kg_export")
MODULES = {
    "extract_course": "pipeline.extract_course",
    "merge": "pipeline.merge",
    "extract_skill": "pipeline.extract_skill",
    "translate": "pipeline.extract_translate.run_extract_translate",
    "skill_matching": "pipeline.skill_matching.pipeline",
    "kg_export": "pipeline.kg_export",
}


def selected_stages(start_at: str, stop_after: str) -> tuple[str, ...]:
    """Return an inclusive, ordered stage range."""
    start = STAGES.index(start_at)
    stop = STAGES.index(stop_after)
    if start > stop:
        raise ValueError("start_at must not come after stop_after.")
    return STAGES[start : stop + 1]


def build_stage_command(
    stage: str,
    config_path: Path,
    *,
    mock_translation: bool = False,
) -> list[str]:
    """Build one argv list without shell interpolation."""
    command = [sys.executable, "-m", MODULES[stage], "--config", str(config_path)]
    if stage == "translate" and mock_translation:
        command.append("--mock")
    return command


def run_pipeline(
    config_path: Path,
    *,
    start_at: str = "extract_course",
    stop_after: str = "kg_export",
    mock_translation: bool = False,
) -> None:
    """Run stages sequentially and stop immediately if a contract or stage fails."""
    for stage in selected_stages(start_at, stop_after):
        command = build_stage_command(stage, config_path, mock_translation=mock_translation)
        LOGGER.info("Running stage %s", stage)
        subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the HaUI KG pipeline in strict stage order.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--start-at", choices=STAGES, default=STAGES[0])
    parser.add_argument("--stop-after", choices=STAGES, default=STAGES[-1])
    parser.add_argument(
        "--mock-translation",
        action="store_true",
        help="Testing only: use the translation mock; never use this output in production.",
    )
    args = parser.parse_args()
    run_pipeline(
        args.config,
        start_at=args.start_at,
        stop_after=args.stop_after,
        mock_translation=args.mock_translation,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()
