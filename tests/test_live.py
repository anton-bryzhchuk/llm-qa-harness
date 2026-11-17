"""Live tests against the real Anthropic API.

Marked @live and skipped automatically when ANTHROPIC_API_KEY is unset, so the
default/mock test run and CI never touch the network.
"""
from __future__ import annotations

import pytest

from llmqa.config import anthropic_api_key
from llmqa.models import Category, Priority

pytestmark = pytest.mark.live

_NO_KEY = anthropic_api_key() is None


@pytest.mark.skipif(_NO_KEY, reason="ANTHROPIC_API_KEY not set; live suite skipped")
def test_live_classify_schema_valid():
    from llmqa.classify import classify_ticket
    from llmqa.providers import make_provider

    provider = make_provider("anthropic")
    res = classify_ticket(
        "I was charged twice for my subscription, please refund the extra payment.",
        provider,
    )
    assert res.valid, f"live output did not validate: {res.error} | {res.raw[:200]!r}"
    assert res.classification is not None
    assert res.classification.category in set(Category)
    assert res.classification.priority in set(Priority)
    assert res.simulated is False


@pytest.mark.skipif(_NO_KEY, reason="ANTHROPIC_API_KEY not set; live suite skipped")
def test_live_billing_is_reasonable():
    from llmqa.classify import classify_ticket
    from llmqa.providers import make_provider

    res = classify_ticket(
        "My invoice is wrong and I was overcharged this month.",
        make_provider("anthropic"),
    )
    assert res.valid
    assert res.category == Category.billing.value
