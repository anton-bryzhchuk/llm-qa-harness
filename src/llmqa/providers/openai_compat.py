"""OpenAI-compatible provider (for local models via Ollama, LM Studio, etc.).

Calls an OpenAI-style ``/v1/chat/completions`` endpoint over httpx. No API key
is required. Configured with:

* ``LLM_BASE_URL`` (default ``http://localhost:11434/v1`` -- Ollama)
* ``LLM_MODEL``    (default ``llama3.2:3b``)

Deliberately does NOT enable JSON mode / constrained output: the schema-contract
suite must observe the model's real formatting behaviour. The pipeline's
existing parse-and-retry logic handles noisy output.

Thinking models: there is no portable OpenAI-compatible switch to disable a
model's reasoning, so any ``<think>...</think>`` block is stripped from the
response text before validation (see ``_strip_think``). ``llama3.2:3b`` has no
thinking mode, so in practice this is a no-op for the default model.
"""
from __future__ import annotations

import re
import time

import httpx

from ..config import llm_base_url, local_model
from .base import Provider, ProviderResponse

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks and surrounding whitespace."""
    return _THINK_RE.sub("", text).strip()


class OpenAICompatibleProvider(Provider):
    name = "local"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 300.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or llm_base_url()).rstrip("/")
        self.model = model or local_model()
        self.timeout = timeout
        self._transport = transport  # injected in tests (MockTransport); None in production

    def complete(self, prompt: str, ticket: str, *, attempt: int = 0) -> ProviderResponse:
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "stream": False,
        }
        started = time.perf_counter()
        with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
            resp = client.post(url, json=body)
        latency_ms = (time.perf_counter() - started) * 1000.0
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices") or [{}]
        message = choices[0].get("message", {}) if choices else {}
        text = _strip_think(message.get("content") or "")

        usage = data.get("usage") or {}
        return ProviderResponse(
            text=text,
            latency_ms=latency_ms,
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            simulated=False,
        )
