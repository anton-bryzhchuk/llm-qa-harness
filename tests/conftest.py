from __future__ import annotations

import pytest

from llmqa.providers import make_provider


@pytest.fixture
def good_make():
    """Factory for a fresh deterministic 'good' mock provider."""
    return lambda: make_provider("mock", profile="good", seed=1234)


def make_mock(profile: str, seed: int = 1234):
    return lambda: make_provider("mock", profile=profile, seed=seed)
