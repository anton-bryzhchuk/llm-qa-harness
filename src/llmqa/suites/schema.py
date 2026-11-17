"""Suite 1 -- schema contract.

Every response must parse as JSON and validate against the Classification
model. Invalid JSON is retried up to MAX_RETRIES times and the retry count is
recorded. Passing means: no parse failures, no schema-invalid outputs.
"""
from __future__ import annotations

from ..classify import classify_ticket
from ..config import MAX_RETRIES
from ..dataset import load_golden
from . import ProviderFactory, SuiteResult


def run_schema(make: ProviderFactory) -> SuiteResult:
    provider = make()
    tickets = load_golden()

    valid = 0
    parse_failures = 0
    retries: list[int] = []
    examples: list[str] = []

    for t in tickets:
        res = classify_ticket(t.text, provider)
        retries.append(res.retries)
        if res.valid:
            valid += 1
        else:
            parse_failures += 1
            if len(examples) < 5:
                snippet = res.raw.replace("\n", " ")[:120]
                examples.append(f"{t.id}: {res.error} | raw={snippet!r}")

    n = len(tickets)
    mean_retries = sum(retries) / n if n else 0.0
    metrics = {
        "n": n,
        "valid": valid,
        "valid_rate": round(valid / n, 4) if n else 0.0,
        "parse_failures": parse_failures,
        "mean_retries": round(mean_retries, 4),
        "max_retries": max(retries) if retries else 0,
        "total_retries": sum(retries),
    }
    passed = parse_failures == 0 and valid == n
    return SuiteResult(
        name="schema_contract",
        passed=passed,
        threshold=f"100% valid JSON (retries allowed up to {MAX_RETRIES})",
        metrics=metrics,
        examples=examples,
    )
