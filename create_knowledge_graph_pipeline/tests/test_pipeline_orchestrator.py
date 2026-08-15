from pathlib import Path

import pytest

from pipeline.run_pipeline import build_stage_command, selected_stages


def test_selected_stages_preserve_required_order() -> None:
    assert selected_stages("merge", "skill_matching") == (
        "merge", "extract_skill", "translate", "skill_matching"
    )


def test_invalid_reverse_stage_range_is_rejected() -> None:
    with pytest.raises(ValueError):
        selected_stages("kg_export", "extract_course")


def test_mock_flag_is_only_added_to_translation_command() -> None:
    config = Path("config.yaml")
    assert "--mock" in build_stage_command("translate", config, mock_translation=True)
    assert "--mock" not in build_stage_command("merge", config, mock_translation=True)
