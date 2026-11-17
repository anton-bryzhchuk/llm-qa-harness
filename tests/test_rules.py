"""Unit tests for the rule-based ground-truth classifier."""
from __future__ import annotations

import pytest

from llmqa import rules
from llmqa.models import Category, Priority


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I was charged twice for my subscription.", Category.billing),
        ("I'm locked out and can't log in.", Category.account_access),
        ("The app crashes with a 500 error.", Category.technical_issue),
        ("It would be nice to have dark mode.", Category.feature_request),
        ("Where is your office located?", Category.other),
    ],
)
def test_category_classification(text, expected):
    assert rules.classify_category(text) == expected


def test_word_boundary_avoids_false_positive():
    # 'download' must not trigger the high-priority keyword 'down'
    cat = rules.classify_category("Could you add CSV download for reports?")
    assert rules.classify_priority("Could you add CSV download for reports?", cat) != Priority.high


def test_language_detection():
    assert rules.detect_language("I cannot log in to my account.") == "en"
    assert rules.detect_language("Ich kann mich nicht anmelden.") == "de"


def test_summary_is_within_limit():
    long_text = "word " * 100
    summary = rules.summarize(long_text)
    assert len(summary) <= 200


def test_summary_handles_empty():
    assert rules.summarize("   ") == "(empty ticket)"


def test_priority_high_on_urgent_access():
    cat = Category.account_access
    assert rules.classify_priority("I am locked out, this is urgent!", cat) == Priority.high


def test_feature_defaults_to_low_priority():
    assert rules.classify_priority("Please add an export option.", Category.feature_request) == Priority.low
