"""``classify_ticket`` -- the system under test.

Renders the versioned prompt, calls a provider, then parses and validates the
JSON response. Invalid JSON is retried up to ``MAX_RETRIES`` times and the retry
count is recorded on the result.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from jinja2 import Template

from .config import DEFAULT_PROMPT, MAX_RETRIES
from .models import Classification
from .providers import Provider, make_provider


@dataclass
class ClassifyResult:
    """Everything one classification call produced, success or not."""

    classification: Classification | None
    raw: str
    retries: int
    valid: bool
    error: str | None
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    simulated: bool

    @property
    def category(self) -> str | None:
        return self.classification.category.value if self.classification else None

    @property
    def priority(self) -> str | None:
        return self.classification.priority.value if self.classification else None


@lru_cache(maxsize=4)
def _load_template(path_str: str) -> Template:
    text = open(path_str, encoding="utf-8").read()  # noqa: SIM115
    return Template(text)


def render_prompt(ticket: str, prompt_path=DEFAULT_PROMPT) -> str:
    return _load_template(str(prompt_path)).render(ticket=ticket)


def extract_json(text: str) -> dict | None:
    """Parse a JSON object from raw model text.

    Tries a direct parse first, then falls back to the substring between the
    first ``{`` and the last ``}`` so a valid object wrapped in prose is still
    recovered. Returns None when nothing parseable is found.
    """
    text = text.strip()
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except (json.JSONDecodeError, ValueError):
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def classify_ticket(
    text: str,
    provider: Provider | None = None,
    *,
    prompt_path=DEFAULT_PROMPT,
    max_retries: int = MAX_RETRIES,
) -> ClassifyResult:
    provider = provider or make_provider("mock", profile="good")
    prompt = render_prompt(text, prompt_path)

    last_error: str | None = None
    last_resp = None

    for attempt in range(max_retries + 1):
        resp = provider.complete(prompt, text, attempt=attempt)
        last_resp = resp
        obj = extract_json(resp.text)
        if obj is None:
            last_error = "unparseable: no JSON object found"
            continue
        try:
            classification = Classification.model_validate(obj)
        except Exception as exc:  # pydantic ValidationError and friends
            last_error = f"schema invalid: {exc.__class__.__name__}"
            continue
        return ClassifyResult(
            classification=classification,
            raw=resp.text,
            retries=attempt,
            valid=True,
            error=None,
            latency_ms=resp.latency_ms,
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
            simulated=resp.simulated,
        )

    # All attempts failed.
    return ClassifyResult(
        classification=None,
        raw=last_resp.text if last_resp else "",
        retries=max_retries,
        valid=False,
        error=last_error,
        latency_ms=last_resp.latency_ms if last_resp else 0.0,
        prompt_tokens=last_resp.prompt_tokens if last_resp else 0,
        completion_tokens=last_resp.completion_tokens if last_resp else 0,
        simulated=last_resp.simulated if last_resp else True,
    )
