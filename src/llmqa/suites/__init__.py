"""Measurement suites.

Each suite is a plain function that takes a provider *factory* (a zero-arg
callable returning a fresh provider) and returns a ``SuiteResult``. Both the
pytest tests and the ``llmqa`` CLI call these same functions, so what the tests
assert and what the report shows can never drift apart.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..providers import Provider

ProviderFactory = Callable[[], Provider]


@dataclass
class SuiteResult:
    name: str
    passed: bool
    threshold: str
    metrics: dict[str, Any]
    examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "threshold": self.threshold,
            "metrics": self.metrics,
            "examples": self.examples,
        }
