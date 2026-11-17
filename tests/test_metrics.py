"""Unit tests for the metric helpers."""
from __future__ import annotations

import pytest

from llmqa.metrics import (
    accuracy,
    accuracy_by_group,
    agreement_rate,
    estimate_cost,
    flakiness_score,
    percentile,
)


def test_accuracy_basic():
    assert accuracy(["a", "b", "c"], ["a", "x", "c"]) == pytest.approx(2 / 3)


def test_accuracy_empty_is_zero():
    assert accuracy([], []) == 0.0


def test_accuracy_length_mismatch_raises():
    with pytest.raises(ValueError):
        accuracy(["a"], ["a", "b"])


def test_accuracy_counts_none_as_wrong():
    assert accuracy([None, "b"], ["a", "b"]) == 0.5


def test_accuracy_by_group():
    pred = ["a", "a", "b", "x"]
    exp = ["a", "a", "b", "b"]
    groups = ["g1", "g1", "g2", "g2"]
    out = accuracy_by_group(pred, exp, groups)
    assert out["g1"] == 1.0
    assert out["g2"] == 0.5


def test_agreement_and_flakiness():
    assert agreement_rate(["a", "a", "a"]) == 1.0
    assert agreement_rate(["a", "a", "b", "c"]) == 0.5
    assert flakiness_score(["a", "a", "b", "c"]) == 0.5
    assert agreement_rate([]) == 0.0


def test_percentile():
    data = [10, 20, 30, 40]
    assert percentile(data, 0) == 10
    assert percentile(data, 100) == 40
    assert percentile(data, 50) == pytest.approx(25.0)
    assert percentile([], 50) == 0.0
    assert percentile([7], 95) == 7.0


def test_estimate_cost_monotonic():
    cheap = estimate_cost(100, 100)
    pricey = estimate_cost(10_000, 10_000)
    assert pricey > cheap > 0
