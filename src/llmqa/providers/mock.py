"""Deterministic mock provider with selectable failure profiles.

Profiles let the harness prove it can *detect* real-world LLM problems without
any API access:

* ``good``       -- correct and stable (the happy path).
* ``flaky``      -- answers wobble between repeated calls (non-determinism).
* ``drifted``    -- billing tickets are systematically mislabelled, simulating
                    a silent regression after a "model update".
* ``injectable`` -- obeys instructions hidden inside the ticket text.
* ``malformed``  -- sometimes emits invalid JSON or wraps JSON in prose.

Every behaviour is a pure function of (profile, seed, ticket, attempt), so test
outcomes are reproducible across runs while still looking "flaky" to the
suites that measure consistency.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict

from .. import rules
from ..models import Category
from .base import Provider, ProviderResponse

PROFILES = ("good", "flaky", "drifted", "injectable", "malformed")

_INJECT_CATEGORY = re.compile(r"category\s*[=:]\s*([a-z_]+)", re.IGNORECASE)
_INJECT_PRIORITY = re.compile(r"priority\s*[=:]\s*([a-z]+)", re.IGNORECASE)
_INJECT_MARKERS = (
    "ignore previous", "ignore all previous", "disregard", "system:",
    "you must", "new instructions", "override",
)


class MockProvider(Provider):
    name = "mock"

    def __init__(self, profile: str = "good", seed: int = 1234) -> None:
        if profile not in PROFILES:
            raise ValueError(f"unknown profile {profile!r}; choose from {PROFILES}")
        self.profile = profile
        self.seed = seed
        self._calls: dict[str, int] = defaultdict(int)

    # -- deterministic helpers ------------------------------------------------
    def _hash(self, *parts: object) -> int:
        raw = "|".join(str(p) for p in (self.seed, *parts))
        return int(hashlib.sha256(raw.encode("utf-8")).hexdigest(), 16)

    def _unit(self, *parts: object) -> float:
        """A deterministic float in [0, 1) keyed by the given parts."""
        return (self._hash(*parts) % 10_000) / 10_000.0

    def _bump(self, ticket: str) -> int:
        idx = self._calls[ticket]
        self._calls[ticket] += 1
        return idx

    # -- profile behaviours ---------------------------------------------------
    def _answer(self, ticket: str, call_idx: int) -> dict[str, str]:
        truth = rules.classify(ticket)

        if self.profile == "good":
            return truth

        if self.profile == "drifted":
            # Silent regression: billing is now mislabelled as "other".
            if truth["category"] == Category.billing.value:
                drifted = dict(truth)
                drifted["category"] = Category.other.value
                return drifted
            return truth

        if self.profile == "flaky":
            # Half the time, swap the category for a different one.
            if self._unit(ticket, call_idx, "flake") < 0.5:
                options = [c.value for c in Category if c.value != truth["category"]]
                pick = self._hash(ticket, call_idx, "pick") % len(options)
                wobbled = dict(truth)
                wobbled["category"] = options[pick]
                return wobbled
            return truth

        if self.profile == "injectable":
            injected = self._read_injection(ticket)
            if injected:
                obeyed = dict(truth)
                obeyed.update(injected)
                return obeyed
            return truth

        # malformed handled in complete(); fall back to truth here.
        return truth

    @staticmethod
    def _read_injection(ticket: str) -> dict[str, str]:
        low = ticket.lower()
        if not any(m in low for m in _INJECT_MARKERS):
            return {}
        out: dict[str, str] = {}
        mcat = _INJECT_CATEGORY.search(ticket)
        if mcat and mcat.group(1).lower() in {c.value for c in Category}:
            out["category"] = mcat.group(1).lower()
        mpri = _INJECT_PRIORITY.search(ticket)
        if mpri and mpri.group(1).lower() in {"low", "medium", "high"}:
            out["priority"] = mpri.group(1).lower()
        return out

    # -- main entry point -----------------------------------------------------
    def complete(self, prompt: str, ticket: str, *, attempt: int = 0) -> ProviderResponse:
        call_idx = self._bump(ticket)
        answer = self._answer(ticket, call_idx)
        payload = json.dumps(answer, ensure_ascii=False)

        text = payload
        if self.profile == "malformed":
            text = self._maybe_break(payload, ticket, attempt)

        # Simulated operational metrics (clearly flagged as simulated).
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(payload) // 4)
        base_latency = 40 + (self._hash(ticket, "lat") % 60)       # 40-99 ms
        jitter = self._hash(ticket, call_idx, "jit") % 25          # 0-24 ms
        latency_ms = float(base_latency + jitter)

        return ProviderResponse(
            text=text,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            simulated=True,
        )

    def _maybe_break(self, payload: str, ticket: str, attempt: int) -> str:
        bucket = self._hash(ticket) % 3
        if bucket == 0:
            # Unrecoverable: invalid JSON on every attempt -> parse failure.
            return payload[:-3] + "  <truncated by model>"
        if bucket == 1:
            # Recoverable noise: valid JSON wrapped in prose. The harness's
            # extraction step should still succeed on the first attempt.
            return f"Sure! Here is the classification:\n{payload}\nLet me know if that helps."
        # bucket == 2: clean on retry -- broken first, valid afterwards. Proves
        # the retry path records a non-zero retry count.
        if attempt == 0:
            return "{not valid json at all"
        return payload
