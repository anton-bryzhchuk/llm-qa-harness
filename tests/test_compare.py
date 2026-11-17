"""Unit tests for the regression-compare logic."""
from __future__ import annotations

import pytest

from llmqa.compare import compare_reports


def _report(accuracy: float, agreement: float) -> dict:
    return {
        "suites": [
            {"name": "golden_accuracy", "metrics": {"accuracy": accuracy}},
            {"name": "consistency", "metrics": {"mean_agreement": agreement}},
        ]
    }


def test_no_change_passes():
    r = _report(0.9, 0.95)
    assert compare_reports(r, r).passed


def test_small_drop_within_tolerance_passes():
    base = _report(0.90, 0.95)
    cur = _report(0.86, 0.90)  # -0.04 accuracy, -0.05 consistency
    assert compare_reports(base, cur).passed


def test_accuracy_drop_beyond_limit_fails():
    base = _report(0.90, 0.95)
    cur = _report(0.80, 0.95)  # -0.10 accuracy
    res = compare_reports(base, cur)
    assert not res.passed


def test_consistency_drop_beyond_limit_fails():
    base = _report(0.90, 0.95)
    cur = _report(0.90, 0.80)  # -0.15 consistency
    res = compare_reports(base, cur)
    assert not res.passed


def test_improvement_passes():
    base = _report(0.80, 0.80)
    cur = _report(0.95, 0.99)
    assert compare_reports(base, cur).passed


def test_missing_metric_raises():
    base = {"suites": [{"name": "golden_accuracy", "metrics": {}}]}
    with pytest.raises(KeyError):
        compare_reports(base, base)
