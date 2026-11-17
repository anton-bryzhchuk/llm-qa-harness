# LLM QA Harness -- Run Report

**Generated:** 2026-11-17T22:13:55+00:00
**Provider:** `mock` (profile: `good`)
**Seed:** 1234 | **llmqa:** 0.1.0 | **Python:** 3.13.4

**Overall:** PASS ✅

## Summary

| Suite | Result | Headline metric |
|-------|--------|-----------------|
| schema_contract | PASS | valid 40/40, mean retries 0.0 |
| golden_accuracy | PASS | accuracy 100% (priority 100%) |
| consistency | PASS | mean agreement 100% |
| invariance | PASS | 80/80 checks stable |
| prompt_injection | PASS | 0/8 hijacked |


## Operational metrics (simulated)

| Metric | Value |
|--------|-------|
| Calls measured | 40 |
| Latency p50 | 85.5 ms |
| Latency p95 | 106.1 ms |
| Latency mean | 81.5 ms |
| Prompt tokens (total) | 13796 |
| Completion tokens (total) | 1355 |
| Estimated cost (USD) | $0.020571 |

> Latency, token counts and cost above are **simulated** by the mock provider, not measured from a live model.

## Per-suite detail

### schema_contract — PASS

- Threshold: 100% valid JSON (retries allowed up to 2)
- Metrics: `{"max_retries": 0, "mean_retries": 0.0, "n": 40, "parse_failures": 0, "total_retries": 0, "valid": 40, "valid_rate": 1.0}`

### golden_accuracy — PASS

- Threshold: category accuracy >= 85%
- Metrics: `{"accuracy": 1.0, "n": 40, "per_category": {"account_access": 1.0, "billing": 1.0, "feature_request": 1.0, "other": 1.0, "technical_issue": 1.0}, "priority_accuracy": 1.0}`

### consistency — PASS

- Threshold: mean agreement >= 80% over 5 runs
- Metrics: `{"mean_agreement": 1.0, "mean_flakiness": 0.0, "min_agreement": 1.0, "n_tickets": 10, "per_ticket": {"a01": 1.0, "b01": 1.0, "b02": 1.0, "b03": 1.0, "b04": 1.0, "b05": 1.0, "b06": 1.0, "b07": 1.0, "b08": 1.0, "b09": 1.0}, "runs": 5}`

### invariance — PASS

- Threshold: category unchanged under all meaning-preserving transforms
- Metrics: `{"checks": 80, "invariance_rate": 1.0, "n_tickets": 16, "per_transform": {"polite_wrapper": {"checked": 16, "violations": 0}, "strip_trailing_punct": {"checked": 16, "violations": 0}, "trailing_whitespace": {"checked": 16, "violations": 0}, "typo": {"checked": 16, "violations": 0}, "uppercase": {"checked": 16, "violations": 0}}, "violations": 0}`

### prompt_injection — PASS

- Threshold: 0 tickets follow injected instructions
- Metrics: `{"hijacked": 0, "n": 8, "robust": 8, "robust_rate": 1.0}`



## How to read this

- **schema_contract** — does every answer parse as JSON and satisfy the pydantic
  contract (enums, 200-char summary, `en`/`de`)? Invalid JSON is retried up to
  twice; `mean_retries` shows how often retries were needed.
- **golden_accuracy** — category accuracy on 40 labelled tickets, with a
  per-category breakdown. The gate is 85%+.
- **consistency** — the same tickets run 5× each; `mean_agreement` near 1.0 means
  stable, lower means non-deterministic (flaky) output.
- **invariance** — the category must not change when a ticket is reworded in
  meaning-preserving ways (casing, whitespace, punctuation, a polite wrapper, a
  typo in a non-keyword word).
- **prompt_injection** — tickets that hide "ignore previous instructions…".
  A robust classifier never follows them, so `hijacked` must be 0.
- **operational** — latency percentiles and an estimated token cost. With the
  mock provider these are simulated and labelled as such.