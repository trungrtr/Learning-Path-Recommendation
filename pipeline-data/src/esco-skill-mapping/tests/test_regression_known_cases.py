"""Regression test to ensure known TPs and FPs are handled correctly."""

import os
from pathlib import Path
import pytest

import sys
sys.path.append(str(Path(__file__).parent.parent))
from evaluation.eval_metrics import calculate_metrics

def test_regression_on_known_cases():
    base_dir = Path(__file__).parent.parent
    gold_csv = base_dir / "evaluation" / "m4_gold_labels.csv"
    output_dir = base_dir / "data" / "skill-teacher"
    
    if not gold_csv.exists():
        pytest.skip("Gold labels CSV not found. Skipping regression test.")
        
    metrics = calculate_metrics(gold_csv, output_dir)
    
    # Assert that all known True Positives are still found
    # (If metrics['total_known_tps'] is 0, this naturally passes, but we expect 7)
    assert metrics['found_tps'] == metrics['total_known_tps'], \
        f"Regression! Expected {metrics['total_known_tps']} TPs, but found {metrics['found_tps']}."
        
    # Assert that known False Positives are successfully filtered out
    # (FP rate should be 0)
    assert metrics['found_fps'] == 0, \
        f"Regression! {metrics['found_fps']} known FPs are still leaking into the TEACHES_SKILL output."

