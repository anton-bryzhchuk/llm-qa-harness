"""Suite 1: schema-contract tests."""
from __future__ import annotations

from conftest import make_mock
from llmqa.suites.schema import run_schema


def test_good_profile_all_valid(good_make):
    res = run_schema(good_make)
    assert res.passed
    assert res.metrics["valid"] == res.metrics["n"] == 40
    assert res.metrics["parse_failures"] == 0
    assert res.metrics["mean_retries"] == 0.0


def test_malformed_profile_is_detected():
    res = run_schema(make_mock("malformed"))
    assert not res.passed
    assert res.metrics["parse_failures"] > 0
    assert res.examples  # failing raw outputs are surfaced
