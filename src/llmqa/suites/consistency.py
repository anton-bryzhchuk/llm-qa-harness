"""Suite 3 -- consistency / non-determinism.

Run each of a fixed sample of tickets N times through one provider instance and
measure how often the category stays the same. A stable model scores ~1.0; a
flaky one scores much lower. Passing means mean agreement >= CONSISTENCY_THRESHOLD.
"""
from __future__ import annotations

from ..classify import classify_ticket
from ..config import CONSISTENCY_RUNS, CONSISTENCY_SAMPLE, CONSISTENCY_THRESHOLD
from ..dataset import load_golden
from ..metrics import agreement_rate
from . import ProviderFactory, SuiteResult


def select_sample(limit: int = CONSISTENCY_SAMPLE) -> list:
    """Deterministically pick a spread of tickets across categories."""
    tickets = load_golden()
    return tickets[:limit]


def run_consistency(
    make: ProviderFactory,
    *,
    runs: int = CONSISTENCY_RUNS,
    sample: int = CONSISTENCY_SAMPLE,
) -> SuiteResult:
    # One provider instance so a flaky profile can vary across repeated calls.
    provider = make()
    tickets = select_sample(sample)

    per_ticket: dict[str, float] = {}
    examples: list[str] = []

    for t in tickets:
        answers = [classify_ticket(t.text, provider).category for _ in range(runs)]
        rate = agreement_rate(answers)
        per_ticket[t.id] = round(rate, 4)
        if rate < 1.0 and len(examples) < 6:
            examples.append(f"{t.id}: answers over {runs} runs = {answers}")

    rates = list(per_ticket.values())
    mean_agreement = sum(rates) / len(rates) if rates else 0.0
    metrics = {
        "runs": runs,
        "n_tickets": len(tickets),
        "mean_agreement": round(mean_agreement, 4),
        "min_agreement": round(min(rates), 4) if rates else 0.0,
        "mean_flakiness": round(1 - mean_agreement, 4),
        "per_ticket": per_ticket,
    }
    passed = mean_agreement >= CONSISTENCY_THRESHOLD
    return SuiteResult(
        name="consistency",
        passed=passed,
        threshold=f"mean agreement >= {CONSISTENCY_THRESHOLD:.0%} over {runs} runs",
        metrics=metrics,
        examples=examples,
    )
