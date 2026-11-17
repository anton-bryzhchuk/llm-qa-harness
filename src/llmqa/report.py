"""Render a run report as JSON and Markdown."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template

from .config import REPORTS_DIR

_MD_TEMPLATE = Template(
    """# LLM QA Harness -- Run Report

**Generated:** {{ meta.generated_at }}
**Provider:** `{{ meta.provider }}`{% if meta.provider == 'mock' %} (profile: `{{ meta.profile }}`){% endif %}
**Seed:** {{ meta.seed }} | **llmqa:** {{ meta.llmqa_version }} | **Python:** {{ meta.python }}

**Overall:** {{ "PASS ✅" if passed else "FAIL ❌" }}

## Summary

| Suite | Result | Headline metric |
|-------|--------|-----------------|
{% for s in suites -%}
| {{ s.name }} | {{ "PASS" if s.passed else "FAIL" }} | {{ headline(s) }} |
{% endfor %}

## Operational metrics{% if operational.simulated %} (simulated){% endif %}

| Metric | Value |
|--------|-------|
| Calls measured | {{ operational.n_calls }} |
| Latency p50 | {{ operational.latency_ms_p50 }} ms |
| Latency p95 | {{ operational.latency_ms_p95 }} ms |
| Latency mean | {{ operational.latency_ms_mean }} ms |
| Prompt tokens (total) | {% if operational.tokens_reported %}{{ operational.total_prompt_tokens }}{% else %}not reported{% endif %} |
| Completion tokens (total) | {% if operational.tokens_reported %}{{ operational.total_completion_tokens }}{% else %}not reported{% endif %} |
| {% if operational.free %}Cost (USD){% else %}Estimated cost (USD){% endif %} | ${{ "%.6f"|format(operational.estimated_cost_usd) }}{% if operational.free %} (free / local){% endif %} |

{% if operational.simulated %}> Latency, token counts and cost above are **simulated** by the mock provider, not measured from a live model.{% elif operational.free %}> Latency is **measured** from a local model. Cost is $0 (runs locally). Token counts are shown only if the endpoint reported them.{% endif %}

## Per-suite detail

{% for s in suites -%}
### {{ s.name }} — {{ "PASS" if s.passed else "FAIL" }}

- Threshold: {{ s.threshold }}
- Metrics: `{{ s.metrics | tojson }}`
{% if s.examples %}- Examples:
{% for ex in s.examples %}  - {{ ex }}
{% endfor %}{% endif %}
{% endfor %}

## How to read this

- **schema_contract** — does every answer parse as JSON and satisfy the pydantic
  contract (enums, 200-char summary, `en`/`de`)? Invalid JSON is retried up to
  twice; `mean_retries` shows how often retries were needed.
- **golden_accuracy** — category accuracy on 40 labelled tickets, with a
  per-category breakdown. The gate is {{ "%.0f"|format(100 * 0.85) }}%+.
- **consistency** — the same tickets run 5× each; `mean_agreement` near 1.0 means
  stable, lower means non-deterministic (flaky) output.
- **invariance** — the category must not change when a ticket is reworded in
  meaning-preserving ways (casing, whitespace, punctuation, a polite wrapper, a
  typo in a non-keyword word).
- **prompt_injection** — tickets that hide "ignore previous instructions…".
  A robust classifier never follows them, so `hijacked` must be 0.
- **operational** — latency percentiles and an estimated token cost. With the
  mock provider these are simulated and labelled as such.
"""
)


def _headline(suite: dict) -> str:
    m = suite["metrics"]
    name = suite["name"]
    if name == "schema_contract":
        return f"valid {m['valid']}/{m['n']}, mean retries {m['mean_retries']}"
    if name == "golden_accuracy":
        return f"accuracy {m['accuracy']:.0%} (priority {m['priority_accuracy']:.0%})"
    if name == "consistency":
        return f"mean agreement {m['mean_agreement']:.0%}"
    if name == "invariance":
        return f"{m['checks'] - m['violations']}/{m['checks']} checks stable"
    if name == "prompt_injection":
        return f"{m['hijacked']}/{m['n']} hijacked"
    return ""


def render_markdown(report: dict) -> str:
    return _MD_TEMPLATE.render(headline=_headline, **report)


def write_reports(report: dict, out_dir: Path = REPORTS_DIR) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "latest.json"
    md_path = out_dir / "latest.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path
