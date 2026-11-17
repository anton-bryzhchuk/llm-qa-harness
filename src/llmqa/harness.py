"""Orchestrates the suites into a single run and assembles a report dict."""
from __future__ import annotations

import platform
from datetime import UTC, datetime

from . import __version__
from .providers import make_provider
from .suites import SuiteResult
from .suites.consistency import run_consistency
from .suites.golden import run_golden
from .suites.injection import run_injection
from .suites.invariance import run_invariance
from .suites.operational import operational_metrics
from .suites.schema import run_schema


def _factory(provider: str, profile: str, seed: int):
    return lambda: make_provider(provider, profile=profile, seed=seed)


def run_all(provider: str = "mock", profile: str = "good", seed: int = 1234) -> dict:
    """Run every suite and return a JSON-serialisable report."""
    make = _factory(provider, profile, seed)

    schema_res = run_schema(make)
    golden_res, samples = run_golden(make)
    consistency_res = run_consistency(make)
    invariance_res = run_invariance(make)
    injection_res = run_injection(make)

    suites: list[SuiteResult] = [
        schema_res,
        golden_res,
        consistency_res,
        invariance_res,
        injection_res,
    ]

    report = {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "llmqa_version": __version__,
            "provider": provider,
            "profile": profile if provider == "mock" else "(n/a)",
            "seed": seed,
            "python": platform.python_version(),
        },
        "passed": all(s.passed for s in suites),
        "suites": [s.to_dict() for s in suites],
        "operational": operational_metrics(samples),
    }
    return report
