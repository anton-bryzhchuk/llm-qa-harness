"""Orchestrates the suites into a single run and assembles a report dict."""
from __future__ import annotations

import platform
import sys
import time
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

# Providers that are free to call (no per-token cost). Mock keeps its clearly
# labelled *simulated* cost estimate; local (Ollama etc.) is genuinely free.
FREE_PROVIDERS = {"local"}


def _factory(provider: str, profile: str, seed: int):
    return lambda: make_provider(provider, profile=profile, seed=seed)


def run_all(provider: str = "mock", profile: str = "good", seed: int = 1234,
            progress: bool = False) -> dict:
    """Run every suite and return a JSON-serialisable report.

    ``progress`` prints a per-suite heartbeat to stderr (useful for slow local
    models); it never touches the returned report, so runs stay deterministic.
    """

    def _step(label, fn):
        if progress:
            print(f"[llmqa] running {label} ...", file=sys.stderr, flush=True)
            t0 = time.perf_counter()
        result = fn()
        if progress:
            dt = time.perf_counter() - t0
            print(f"[llmqa]   {label} done in {dt:.1f}s", file=sys.stderr, flush=True)
        return result

    make = _factory(provider, profile, seed)

    schema_res = _step("schema_contract", lambda: run_schema(make))
    golden_res, samples = _step("golden_accuracy", lambda: run_golden(make))
    consistency_res = _step("consistency", lambda: run_consistency(make))
    invariance_res = _step("invariance", lambda: run_invariance(make))
    injection_res = _step("prompt_injection", lambda: run_injection(make))

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
        "operational": operational_metrics(samples, free=provider in FREE_PROVIDERS),
    }
    return report
