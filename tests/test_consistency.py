"""Suite 3: consistency / non-determinism tests."""
from __future__ import annotations

from conftest import make_mock
from llmqa.config import CONSISTENCY_THRESHOLD
from llmqa.suites.consistency import run_consistency


def test_good_profile_is_stable(good_make):
    res = run_consistency(good_make)
    assert res.passed
    assert res.metrics["mean_agreement"] == 1.0
    assert res.metrics["mean_flakiness"] == 0.0


def test_flaky_profile_is_detected():
    res = run_consistency(make_mock("flaky"))
    assert not res.passed
    assert res.metrics["mean_agreement"] < CONSISTENCY_THRESHOLD
    assert res.examples
