"""A small deterministic rule-based classifier.

This is the "ground truth engine" the MockProvider uses to produce plausible,
*correct* answers without calling a real model. It is intentionally simple
keyword matching: enough to give the golden dataset a stable expected answer,
and cheap enough to run thousands of times in tests.

It is NOT presented as a real classifier -- it exists so the harness can be
exercised deterministically and offline.
"""
from __future__ import annotations

import re

from .models import Category, Priority

# Order matters: the first category whose keywords match wins.
_CATEGORY_KEYWORDS: list[tuple[Category, tuple[str, ...]]] = [
    (
        Category.account_access,
        (
            "log in", "login", "logging in", "sign in", "signin", "signed in",
            "log into", "password", "reset my password", "locked out", "locked",
            "can't access my account", "cannot access my account", "2fa",
            "two-factor", "authenticator", "verification code",
            # German
            "anmelden", "einloggen", "anmeldung", "passwort", "kennwort",
            "gesperrt", "zugang", "zugriff auf mein konto", "bestätigungscode",
        ),
    ),
    (
        Category.billing,
        (
            "invoice", "charged", "charge", "refund", "refunded", "payment",
            "paid", "subscription", "renewal", "renew",
            "credit card", "overcharged", "double charged", "double-charged",
            "receipt", "pricing", "price",
            # German
            "rechnung", "zahlung", "bezahlt", "erstattung", "abo", "abonnement",
            "kreditkarte", "preis", "gebühr", "abgebucht", "zahlungsmethode",
            "berechnet",
        ),
    ),
    (
        Category.feature_request,
        (
            "would be nice", "please add", "add support", "feature request",
            "suggestion", "i wish", "it would help", "export option",
            "dark mode", "could you add", "can you add", "add an option",
            # German
            "wäre schön", "bitte fügt", "vorschlag", "wunsch", "hinzufügen",
            "könntet ihr", "funktion hinzufügen",
        ),
    ),
    (
        Category.technical_issue,
        (
            "error", "crash", "crashes", "bug", "not working",
            "doesn't work", "does not work", "broken", "fails", "failing",
            "freeze", "frozen", "exception", "glitch", "won't load",
            "blank screen", "500", "timeout", "very slow",
            # German
            "fehler", "absturz", "stürzt ab", "funktioniert nicht",
            "geht nicht", "kaputt", "lädt nicht", "hängt", "fehlermeldung",
        ),
    ),
]

_HIGH_PRIORITY = (
    "urgent", "asap", "immediately", "right now", "locked out",
    "can't access", "cannot access", "outage", "down", "production",
    "losing money", "charged twice", "double charged", "double-charged",
    "overcharged", "security", "breach", "data loss", "blocked", "today",
    # German
    "dringend", "sofort", "gesperrt", "kein zugriff", "ausfall",
    "doppelt abgebucht", "sicherheit", "notfall",
)

_LOW_PRIORITY = (
    "would be nice", "suggestion", "just wondering", "just curious",
    "quick question", "minor", "typo", "cosmetic", "no rush", "whenever",
    "i wish", "nice to have",
    # German
    "wäre schön", "vorschlag", "kleinigkeit", "kein stress", "irgendwann",
)

# A few strong German signals used for language detection.
_GERMAN_SIGNALS = (
    "ä", "ö", "ü", "ß", " ich ", " nicht", " kann", " mein", " und ",
    " ist ", " wurde", "rechnung", "passwort", "funktioniert", "gesperrt",
    "danke", "bitte", "könnt", "wäre", "fehler",
)


def _compile(keywords: tuple[str, ...]) -> re.Pattern[str]:
    # Word-boundary match so short keywords like "down" don't fire inside
    # "download", and "fehler" doesn't fire inside unrelated words.
    alts = "|".join(re.escape(kw) for kw in keywords)
    return re.compile(rf"(?<!\w)(?:{alts})(?!\w)", re.IGNORECASE)


_CATEGORY_PATTERNS = [(cat, _compile(kws)) for cat, kws in _CATEGORY_KEYWORDS]
_HIGH_PATTERN = _compile(_HIGH_PRIORITY)
_LOW_PATTERN = _compile(_LOW_PRIORITY)


def detect_language(text: str) -> str:
    low = f" {text.lower()} "
    if any(sig in low for sig in _GERMAN_SIGNALS):
        return "de"
    return "en"


def classify_category(text: str) -> Category:
    for category, pattern in _CATEGORY_PATTERNS:
        if pattern.search(text):
            return category
    return Category.other


def classify_priority(text: str, category: Category) -> Priority:
    if _HIGH_PATTERN.search(text):
        return Priority.high
    if _LOW_PATTERN.search(text):
        return Priority.low
    if category == Category.feature_request:
        return Priority.low
    return Priority.medium


def summarize(text: str) -> str:
    """Produce a neutral one-sentence summary within the 200-char limit."""
    collapsed = re.sub(r"\s+", " ", text).strip()
    first = re.split(r"(?<=[.!?])\s", collapsed, maxsplit=1)[0]
    summary = first if first else collapsed
    if len(summary) > 200:
        summary = summary[:197].rstrip() + "..."
    return summary or "(empty ticket)"


def classify(text: str) -> dict[str, str]:
    """Return the full ground-truth answer as plain strings."""
    category = classify_category(text)
    priority = classify_priority(text, category)
    return {
        "category": category.value,
        "priority": priority.value,
        "summary": summarize(text),
        "language": detect_language(text),
    }
