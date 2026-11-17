"""Suite 2: golden-accuracy tests."""
from __future__ import annotations

from conftest import make_mock
from llmqa.config import ACCURACY_THRESHOLD
from llmqa.suites.golden import run_golden


def test_good_profile_meets_threshold(good_make):
    res, samples = run_golden(good_make)
    assert res.passed
    assert res.metrics["accuracy"] >= ACCURACY_THRESHOLD
    assert len(samples) == 40
    # every category is represented in the per-category breakdown
    assert set(res.metrics["per_category"]) == {
        "billing",
        "technical_issue",
        "account_access",
        "feature_request",
        "other",
    }


def test_drift_regression_is_detected():
    res, _ = run_golden(make_mock("drifted"))
    assert not res.passed
    assert res.metrics["accuracy"] < ACCURACY_THRESHOLD
    # the mislabelled category is billing
    assert res.metrics["per_category"]["billing"] == 0.0
