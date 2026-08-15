"""Fail-fast orchestrator for the programme-level CTDT pipeline."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from pipeline.extract_course.cau_hinh import DEFAULT_CONFIG

LOGGER = logging.getLogger(__name__)
STAGES = ("extract_ctdt", "kg_export_ctdt")
MODULES = {
    "extract_ctdt": "pipeline.extract_ctdt",
    "kg_export_ctdt": "pipeline.kg_export.ctdt",
}


def selected_stages(start_at: str, stop_after: str) -> tuple[str, ...]:
    start = STAGES.index(start_at)
    stop = STAGES.index(stop_after)
    if start > stop:
        raise ValueError("start_at must not come after stop_after.")
    return STAGES[start : stop + 1]


def build_stage_command(stage: str, config_path: Path) -> list[str]:
    return [sys.executable, "-m", MODULES[stage], "--config", str(config_path)]


def run_pipeline(
    config_path: Path,
    *,
    start_at: str = "extract_ctdt",
    stop_after: str = "kg_export_ctdt",
) -> None:
    for stage in selected_stages(start_at, stop_after):
        command = build_stage_command(stage, config_path)
        LOGGER.info("Running CTDT stage %s", stage)
        subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CTDT pipeline in strict stage order.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--start-at", choices=STAGES, default=STAGES[0])
    parser.add_argument("--stop-after", choices=STAGES, default=STAGES[-1])
    args = parser.parse_args()
    run_pipeline(args.config, start_at=args.start_at, stop_after=args.stop_after)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    main()

