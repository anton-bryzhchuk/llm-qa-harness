"""Provider factory."""
from __future__ import annotations

from .base import Provider, ProviderResponse
from .mock import PROFILES, MockProvider

__all__ = [
    "Provider",
    "ProviderResponse",
    "MockProvider",
    "PROFILES",
    "make_provider",
]


def make_provider(kind: str = "mock", *, profile: str = "good", seed: int = 1234) -> Provider:
    """Build a provider by name. ``anthropic`` is imported lazily so that the
    mock path never requires httpx credentials to be present."""
    if kind == "mock":
        return MockProvider(profile=profile, seed=seed)
    if kind == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider()
    if kind == "local":
        from .openai_compat import OpenAICompatibleProvider

        return OpenAICompatibleProvider()
    raise ValueError(f"unknown provider {kind!r}; choose 'mock', 'anthropic' or 'local'")
