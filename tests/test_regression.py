"""Suite 6: regression-gate tests (end to end over real reports)."""
from __future__ import annotations

from llmqa.compare import compare_reports
from llmqa.harness import run_all


def test_identical_run_passes_gate():
    good = run_all(profile="good")
    assert compare_reports(good, good).passed


def test_drift_fails_the_gate():
    baseline = run_all(profile="good")
    current = run_all(profile="drifted")
    result = compare_reports(baseline, current)
    assert not result.passed
    acc_check = next(c for c in result.checks if c["metric"] == "accuracy")
    assert not acc_check["ok"]
    assert acc_check["delta"] < -0.05


def test_flaky_fails_consistency_gate():
    baseline = run_all(profile="good")
    current = run_all(profile="flaky")
    result = compare_reports(baseline, current)
    assert not result.passed
    con_check = next(
        c for c in result.checks if c["metric"] == "consistency_mean_agreement"
    )
    assert not con_check["ok"]
