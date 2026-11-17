"""Anthropic Messages API provider (used only by the @live suite).

Reads ANTHROPIC_API_KEY and LLM_MODEL from the environment. The key is never
logged or persisted. If httpx or the key is missing, construction fails loudly
so live tests skip rather than silently passing.
"""
from __future__ import annotations

import time

import httpx

from ..config import DEFAULT_MODEL, anthropic_api_key
from .base import Provider, ProviderResponse

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str | None = None, timeout: float = 30.0) -> None:
        key = anthropic_api_key()
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set; cannot use AnthropicProvider")
        self._key = key
        self.model = model or DEFAULT_MODEL
        self.timeout = timeout

    def complete(self, prompt: str, ticket: str, *, attempt: int = 0) -> ProviderResponse:
        headers = {
            "x-api-key": self._key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": 512,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}],
        }
        started = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(API_URL, headers=headers, json=body)
        latency_ms = (time.perf_counter() - started) * 1000.0
        resp.raise_for_status()
        data = resp.json()

        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return ProviderResponse(
            text=text,
            latency_ms=latency_ms,
            prompt_tokens=int(usage.get("input_tokens", 0)),
            completion_tokens=int(usage.get("output_tokens", 0)),
            simulated=False,
        )
