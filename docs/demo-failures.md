# Demo: the harness detects injected failures

Each mock profile injects a specific, realistic LLM failure. This table
shows which suite caught it. A green run means every failure was detected
by the tests (i.e. the QA harness actually works).

**Result:** all failures detected ✅

| Profile | Failure injected | Caught by | Detected | Key metric |
|---------|------------------|-----------|----------|------------|
| `flaky` | mean agreement drops below threshold | `consistency` | yes | mean_agreement=0.56 |
| `drifted` | billing mislabelled -> accuracy drops | `golden_accuracy` | yes | accuracy=0.775 |
| `injectable` | follows hidden instructions -> hijacked > 0 | `prompt_injection` | yes | hijacked=8/8 |
| `malformed` | invalid JSON survives retries -> parse failures | `schema_contract` | yes | parse_failures=18 |

