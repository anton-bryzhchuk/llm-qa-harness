"""Suite 2 -- golden-dataset accuracy.

Classify all 40 golden tickets and compare the predicted category (the headline
metric) and priority against the expected labels. Reports accuracy per
category. Passing means category accuracy >= ACCURACY_THRESHOLD.

Also returns the raw per-ticket latency/token samples so the runner can compute
operational metrics without a second pass.
"""
from __future__ import annotations

from ..classify import classify_ticket
from ..config import ACCURACY_THRESHOLD
from ..dataset import load_golden
from ..metrics import accuracy, accuracy_by_group
from . import ProviderFactory, SuiteResult


def run_golden(make: ProviderFactory) -> tuple[SuiteResult, list[dict]]:
    provider = make()
    tickets = load_golden()

    pred_cat: list[str | None] = []
    pred_pri: list[str | None] = []
    exp_cat: list[str] = []
    exp_pri: list[str] = []
    samples: list[dict] = []
    examples: list[str] = []

    for t in tickets:
        res = classify_ticket(t.text, provider)
        pred_cat.append(res.category)
        pred_pri.append(res.priority)
        exp_cat.append(t.category)
        exp_pri.append(t.priority)
        samples.append(
            {
                "latency_ms": res.latency_ms,
                "prompt_tokens": res.prompt_tokens,
                "completion_tokens": res.completion_tokens,
                "simulated": res.simulated,
            }
        )
        if res.category != t.category and len(examples) < 6:
            examples.append(
                f"{t.id}: expected {t.category}, got {res.category} "
                f"(text: {t.text[:50]!r})"
            )

    cat_acc = accuracy(pred_cat, exp_cat)
    pri_acc = accuracy(pred_pri, exp_pri)
    per_cat = accuracy_by_group(pred_cat, exp_cat, exp_cat)

    metrics = {
        "n": len(tickets),
        "accuracy": round(cat_acc, 4),
        "priority_accuracy": round(pri_acc, 4),
        "per_category": {k: round(v, 4) for k, v in sorted(per_cat.items())},
    }
    passed = cat_acc >= ACCURACY_THRESHOLD
    result = SuiteResult(
        name="golden_accuracy",
        passed=passed,
        threshold=f"category accuracy >= {ACCURACY_THRESHOLD:.0%}",
        metrics=metrics,
        examples=examples,
    )
    return result, samples
