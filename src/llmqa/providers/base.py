"""Provider abstraction: anything that turns a prompt into raw text."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResponse:
    """Raw output of one model call plus operational metadata.

    ``simulated`` is True when latency / token counts are fabricated by a mock
    rather than measured from a real API call. The reports surface this flag so
    nobody mistakes simulated numbers for live ones.
    """

    text: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    simulated: bool


class Provider(ABC):
    """Common interface implemented by MockProvider and AnthropicProvider."""

    name: str = "provider"

    @abstractmethod
    def complete(self, prompt: str, ticket: str, *, attempt: int = 0) -> ProviderResponse:
        """Return a raw text completion for ``prompt``.

        ``ticket`` is passed separately so the mock can reason about the ticket
        directly; real providers only need ``prompt`` (which already embeds the
        ticket). ``attempt`` is the retry index, letting a mock vary its answer
        across retries.
        """
        raise NotImplementedError
