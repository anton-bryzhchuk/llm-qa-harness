"""Suite 5: prompt-injection robustness tests."""
from __future__ import annotations

from conftest import make_mock
from llmqa.suites.injection import run_injection


def test_good_profile_ignores_injections(good_make):
    res = run_injection(good_make)
    assert res.passed
    assert res.metrics["hijacked"] == 0
    assert res.metrics["n"] == 8


def test_injectable_profile_is_detected():
    res = run_injection(make_mock("injectable"))
    assert not res.passed
    assert res.metrics["hijacked"] > 0
    assert res.examples
