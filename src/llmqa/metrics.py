"""Pure metric helpers: accuracy, agreement/flakiness, latency, cost.

Kept dependency-free and side-effect-free so they are trivial to unit test.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from .config import PRICE_INPUT_PER_MTOK, PRICE_OUTPUT_PER_MTOK


def accuracy(predicted: Sequence[str | None], expected: Sequence[str]) -> float:
    if not expected:
        return 0.0
    if len(predicted) != len(expected):
        raise ValueError("predicted and expected must be the same length")
    correct = sum(1 for p, e in zip(predicted, expected, strict=True) if p == e)
    return correct / len(expected)


def accuracy_by_group(
    predicted: Sequence[str | None],
    expected: Sequence[str],
    groups: Sequence[str],
) -> dict[str, float]:
    """Accuracy bucketed by a grouping key (e.g. expected category)."""
    totals: Counter[str] = Counter()
    hits: Counter[str] = Counter()
    for p, e, g in zip(predicted, expected, groups, strict=True):
        totals[g] += 1
        if p == e:
            hits[g] += 1
    return {g: hits[g] / totals[g] for g in totals}


def agreement_rate(answers: Sequence[str | None]) -> float:
    """Fraction of answers equal to the single most common answer.

    1.0 means perfectly consistent; lower means the model wobbled.
    """
    if not answers:
        return 0.0
    counts = Counter(answers)
    return counts.most_common(1)[0][1] / len(answers)


def flakiness_score(answers: Sequence[str | None]) -> float:
    """1 - agreement_rate: 0 is perfectly stable, higher is flakier."""
    return 1.0 - agreement_rate(answers)


def percentile(values: Sequence[float], pct: float) -> float:
    """Linear-interpolation percentile (pct in [0, 100])."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = (pct / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return float(ordered[low] + (ordered[high] - ordered[low]) * frac)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Estimated USD cost for the given token counts."""
    return (
        prompt_tokens / 1_000_000 * PRICE_INPUT_PER_MTOK
        + completion_tokens / 1_000_000 * PRICE_OUTPUT_PER_MTOK
    )
