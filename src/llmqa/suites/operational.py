"""Suite 7 -- operational metrics.

Latency p50/p95 and estimated token cost, aggregated from the per-ticket
samples collected during the golden run. For the mock provider these numbers
are simulated and flagged as such.
"""
from __future__ import annotations

from ..metrics import estimate_cost, percentile


def operational_metrics(samples: list[dict]) -> dict:
    latencies = [s["latency_ms"] for s in samples]
    prompt_tokens = sum(s["prompt_tokens"] for s in samples)
    completion_tokens = sum(s["completion_tokens"] for s in samples)
    simulated = any(s.get("simulated", False) for s in samples)

    total_cost = estimate_cost(prompt_tokens, completion_tokens)
    n = len(samples)
    return {
        "n_calls": n,
        "latency_ms_p50": round(percentile(latencies, 50), 2),
        "latency_ms_p95": round(percentile(latencies, 95), 2),
        "latency_ms_mean": round(sum(latencies) / n, 2) if n else 0.0,
        "total_prompt_tokens": prompt_tokens,
        "total_completion_tokens": completion_tokens,
        "estimated_cost_usd": round(total_cost, 6),
        "simulated": simulated,
    }
