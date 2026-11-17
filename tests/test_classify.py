"""Unit tests for classify_ticket: JSON extraction and retry logic."""
from __future__ import annotations

from llmqa.classify import classify_ticket, extract_json
from llmqa.providers.base import Provider, ProviderResponse


def _resp(text: str) -> ProviderResponse:
    return ProviderResponse(text=text, latency_ms=1.0, prompt_tokens=1, completion_tokens=1, simulated=True)


class ScriptedProvider(Provider):
    """Returns a preset response per attempt index."""

    name = "scripted"

    def __init__(self, texts: list[str]):
        self.texts = texts
        self.calls = 0

    def complete(self, prompt: str, ticket: str, *, attempt: int = 0) -> ProviderResponse:
        self.calls += 1
        idx = min(attempt, len(self.texts) - 1)
        return _resp(self.texts[idx])


_VALID = '{"category":"billing","priority":"low","summary":"x","language":"en"}'


def test_extract_direct_json():
    assert extract_json(_VALID)["category"] == "billing"


def test_extract_json_from_prose():
    wrapped = f"Sure, here you go:\n{_VALID}\nHope that helps!"
    assert extract_json(wrapped)["priority"] == "low"


def test_extract_returns_none_for_garbage():
    assert extract_json("not json at all") is None
    assert extract_json("{broken") is None


def test_success_on_first_attempt_has_zero_retries():
    res = classify_ticket("ignored", ScriptedProvider([_VALID]))
    assert res.valid
    assert res.retries == 0
    assert res.category == "billing"


def test_retry_recovers_and_records_count():
    provider = ScriptedProvider(["{bad", "still bad", _VALID])
    res = classify_ticket("ignored", provider, max_retries=2)
    assert res.valid
    assert res.retries == 2
    assert provider.calls == 3


def test_gives_up_after_max_retries():
    provider = ScriptedProvider(["{bad", "{bad", "{bad", _VALID])
    res = classify_ticket("ignored", provider, max_retries=2)
    assert not res.valid
    assert res.retries == 2
    assert res.classification is None
    assert res.error is not None
    assert provider.calls == 3  # only 1 + 2 retries, never reaches the valid 4th


def test_schema_invalid_is_rejected():
    bad_enum = '{"category":"nope","priority":"low","summary":"x","language":"en"}'
    res = classify_ticket("ignored", ScriptedProvider([bad_enum]), max_retries=0)
    assert not res.valid
    assert "schema invalid" in (res.error or "")


def test_summary_over_200_chars_is_invalid():
    long_summary = "a" * 201
    bad = f'{{"category":"other","priority":"low","summary":"{long_summary}","language":"en"}}'
    res = classify_ticket("ignored", ScriptedProvider([bad]), max_retries=0)
    assert not res.valid
