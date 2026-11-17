"""Unit tests for the OpenAI-compatible (local) provider.

Uses httpx.MockTransport so no network is touched (safe for CI).
"""
from __future__ import annotations

import json

import httpx
import pytest

from llmqa.providers import make_provider
from llmqa.providers.openai_compat import OpenAICompatibleProvider, _strip_think


def _transport(payload: dict, capture: dict | None = None) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if capture is not None:
            capture["url"] = str(request.url)
            capture["body"] = json.loads(request.content)
        return httpx.Response(200, json=payload)

    return httpx.MockTransport(handler)


_OK = '{"category":"billing","priority":"low","summary":"x","language":"en"}'


def _resp(content: str, usage: dict | None = None) -> dict:
    out = {"choices": [{"message": {"role": "assistant", "content": content}}]}
    if usage is not None:
        out["usage"] = usage
    return out


def test_strip_think_removes_reasoning():
    assert _strip_think("<think>hmm let me see</think>\n" + _OK) == _OK
    assert _strip_think("no think here") == "no think here"


def test_parses_content_and_usage():
    payload = _resp(_OK, usage={"prompt_tokens": 120, "completion_tokens": 25})
    provider = OpenAICompatibleProvider(transport=_transport(payload))
    r = provider.complete("prompt", "ticket")
    assert r.text == _OK
    assert r.prompt_tokens == 120
    assert r.completion_tokens == 25
    assert r.simulated is False
    assert r.latency_ms >= 0


def test_strips_think_from_live_response():
    payload = _resp("<think>should this be billing?</think>" + _OK)
    provider = OpenAICompatibleProvider(transport=_transport(payload))
    assert provider.complete("p", "t").text == _OK


def test_missing_usage_yields_zero_tokens():
    provider = OpenAICompatibleProvider(transport=_transport(_resp(_OK)))
    r = provider.complete("p", "t")
    assert r.prompt_tokens == 0
    assert r.completion_tokens == 0


def test_uses_env_base_url_and_model(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://example.test:9999/v1")
    monkeypatch.setenv("LLM_MODEL", "my-model:1b")
    capture: dict = {}
    provider = OpenAICompatibleProvider(transport=_transport(_resp(_OK), capture))
    provider.complete("my prompt", "t")
    assert capture["url"] == "http://example.test:9999/v1/chat/completions"
    assert capture["body"]["model"] == "my-model:1b"
    assert capture["body"]["messages"][0]["content"] == "my prompt"
    # JSON mode / constrained output must NOT be enabled.
    assert "response_format" not in capture["body"]


def test_default_base_url_is_ollama(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    provider = OpenAICompatibleProvider()
    assert provider.base_url == "http://localhost:11434/v1"


def test_factory_builds_local():
    assert isinstance(make_provider("local"), OpenAICompatibleProvider)


def test_factory_unknown_still_raises():
    with pytest.raises(ValueError):
        make_provider("nope")
