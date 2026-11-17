"""Suite 4 -- invariance / metamorphic tests.

A robust classifier should give the same category when the ticket is reworded
in meaning-preserving ways: changed casing, trailing whitespace, light
punctuation changes, a polite wrapper, and a typo in a non-keyword word. Each
transform is applied to a sample of tickets and the category must not change
relative to the untransformed ticket.
"""
from __future__ import annotations

import re

from ..classify import classify_ticket
from ..dataset import load_golden
from . import ProviderFactory, SuiteResult

_SAFE_TYPO_SKIP = "__no_safe_token__"


def t_upper(text: str) -> str:
    return text.upper()


def t_trailing_ws(text: str) -> str:
    return text + "   \t\n  "


def t_strip_punct(text: str) -> str:
    return re.sub(r"[.!?]+\s*$", "", text).strip()


def t_polite_wrapper(text: str) -> str:
    return f"Hi team, {text} Thanks in advance."


def t_typo(text: str, keyword_pattern: re.Pattern[str]) -> str:
    """Double the middle character of the first word that is not part of any
    keyword, so the category signal is preserved but the string changes."""
    for word in re.findall(r"[A-Za-zÀ-ÿ]+", text):
        if len(word) < 4:
            continue
        if keyword_pattern.search(word):
            continue
        mid = len(word) // 2
        typo = word[:mid] + word[mid] + word[mid:]
        return text.replace(word, typo, 1)
    return _SAFE_TYPO_SKIP


# One combined pattern of every category/priority keyword, used to keep the
# typo transform away from meaning-bearing words.
def _keyword_guard() -> re.Pattern[str]:
    from ..rules import _CATEGORY_KEYWORDS, _HIGH_PRIORITY, _LOW_PRIORITY

    words: set[str] = set()
    for _, kws in _CATEGORY_KEYWORDS:
        for kw in kws:
            words.update(kw.split())
    for kw in (*_HIGH_PRIORITY, *_LOW_PRIORITY):
        words.update(kw.split())
    alts = "|".join(sorted((re.escape(w) for w in words), key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alts})(?!\w)", re.IGNORECASE)


def run_invariance(make: ProviderFactory, *, sample: int = 16) -> SuiteResult:
    provider = make()
    tickets = load_golden()[:sample]
    guard = _keyword_guard()

    transforms = [
        ("uppercase", t_upper),
        ("trailing_whitespace", t_trailing_ws),
        ("strip_trailing_punct", t_strip_punct),
        ("polite_wrapper", t_polite_wrapper),
        ("typo", lambda s: t_typo(s, guard)),
    ]

    total = 0
    violations = 0
    examples: list[str] = []
    per_transform: dict[str, dict[str, int]] = {
        name: {"checked": 0, "violations": 0} for name, _ in transforms
    }

    for t in tickets:
        base = classify_ticket(t.text, provider).category
        for name, fn in transforms:
            variant = fn(t.text)
            if variant == _SAFE_TYPO_SKIP:
                continue
            got = classify_ticket(variant, provider).category
            total += 1
            per_transform[name]["checked"] += 1
            if got != base:
                violations += 1
                per_transform[name]["violations"] += 1
                if len(examples) < 6:
                    examples.append(
                        f"{t.id}/{name}: {base} -> {got}"
                    )

    invariance_rate = (total - violations) / total if total else 0.0
    metrics = {
        "n_tickets": len(tickets),
        "checks": total,
        "violations": violations,
        "invariance_rate": round(invariance_rate, 4),
        "per_transform": per_transform,
    }
    passed = violations == 0
    return SuiteResult(
        name="invariance",
        passed=passed,
        threshold="category unchanged under all meaning-preserving transforms",
        metrics=metrics,
        examples=examples,
    )
