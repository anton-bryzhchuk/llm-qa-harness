"""Suite 6 -- regression gate.

Compare a current run's metrics against an accepted baseline. The gate fails if
accuracy drops by more than ACCURACY_DROP_LIMIT or consistency (mean agreement)
drops by more than CONSISTENCY_DROP_LIMIT.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .config import ACCURACY_DROP_LIMIT, CONSISTENCY_DROP_LIMIT


@dataclass
class CompareResult:
    passed: bool
    checks: list[dict]

    def render(self) -> str:
        lines = []
        for c in self.checks:
            status = "OK" if c["ok"] else "FAIL"
            lines.append(
                f"[{status}] {c['metric']}: baseline={c['baseline']:.4f} "
                f"current={c['current']:.4f} delta={c['delta']:+.4f} "
                f"(limit drop {c['limit']:.4f})"
            )
        verdict = "PASS" if self.passed else "FAIL"
        lines.append(f"Regression gate: {verdict}")
        return "\n".join(lines)


def _metric(report: dict, suite: str, key: str) -> float:
    for s in report.get("suites", []):
        if s["name"] == suite:
            return float(s["metrics"][key])
    raise KeyError(f"metric {suite}.{key} not found in report")


def compare_reports(baseline: dict, current: dict) -> CompareResult:
    checks: list[dict] = []

    base_acc = _metric(baseline, "golden_accuracy", "accuracy")
    cur_acc = _metric(current, "golden_accuracy", "accuracy")
    acc_delta = cur_acc - base_acc
    checks.append(
        {
            "metric": "accuracy",
            "baseline": base_acc,
            "current": cur_acc,
            "delta": acc_delta,
            "limit": ACCURACY_DROP_LIMIT,
            "ok": acc_delta >= -ACCURACY_DROP_LIMIT,
        }
    )

    base_con = _metric(baseline, "consistency", "mean_agreement")
    cur_con = _metric(current, "consistency", "mean_agreement")
    con_delta = cur_con - base_con
    checks.append(
        {
            "metric": "consistency_mean_agreement",
            "baseline": base_con,
            "current": cur_con,
            "delta": con_delta,
            "limit": CONSISTENCY_DROP_LIMIT,
            "ok": con_delta >= -CONSISTENCY_DROP_LIMIT,
        }
    )

    passed = all(c["ok"] for c in checks)
    return CompareResult(passed=passed, checks=checks)


def load_report(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
