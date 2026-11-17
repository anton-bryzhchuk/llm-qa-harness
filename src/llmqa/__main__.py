"""Command-line entry point: ``python -m llmqa ...``."""
from __future__ import annotations

import argparse
import json
import sys

from .compare import compare_reports, load_report
from .config import BASELINES_DIR, DOCS_DIR, REPORTS_DIR
from .harness import run_all
from .report import render_markdown, write_reports

# Which suite each failure profile is expected to trip, and how to read it.
_DEMO_EXPECTATIONS = {
    "flaky": ("consistency", "mean agreement drops below threshold"),
    "drifted": ("golden_accuracy", "billing mislabelled -> accuracy drops"),
    "injectable": ("prompt_injection", "follows hidden instructions -> hijacked > 0"),
    "malformed": ("schema_contract", "invalid JSON survives retries -> parse failures"),
}


def _suite(report: dict, name: str) -> dict:
    for s in report["suites"]:
        if s["name"] == name:
            return s
    raise KeyError(name)


def cmd_run(args: argparse.Namespace) -> int:
    report = run_all(provider=args.provider, profile=args.profile, seed=args.seed, progress=True)
    json_path, md_path = write_reports(report, REPORTS_DIR)
    print(render_markdown(report))
    print(f"\nWrote {json_path} and {md_path}")
    return 0 if report["passed"] else 1


def cmd_compare(args: argparse.Namespace) -> int:
    baseline = load_report(args.baseline)
    current = load_report(args.current)
    result = compare_reports(baseline, current)
    print(result.render())
    return 0 if result.passed else 1


def cmd_demo_failures(args: argparse.Namespace) -> int:
    rows = []
    all_detected = True
    for profile, (suite_name, why) in _DEMO_EXPECTATIONS.items():
        report = run_all(provider="mock", profile=profile, seed=args.seed)
        suite = _suite(report, suite_name)
        detected = not suite["passed"]
        all_detected = all_detected and detected
        rows.append(
            {
                "profile": profile,
                "suite": suite_name,
                "detected": detected,
                "why": why,
                "metrics": suite["metrics"],
            }
        )
        status = "DETECTED" if detected else "MISSED"
        print(f"[{status}] profile={profile:10s} via {suite_name}: {why}")

    _write_demo_doc(rows, all_detected)
    print()
    print("All failures detected ✅" if all_detected else "Some failures were MISSED ❌")
    return 0 if all_detected else 1


def _write_demo_doc(rows: list[dict], all_detected: bool) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Demo: the harness detects injected failures",
        "",
        "Each mock profile injects a specific, realistic LLM failure. This table",
        "shows which suite caught it. A green run means every failure was detected",
        "by the tests (i.e. the QA harness actually works).",
        "",
        f"**Result:** {'all failures detected ✅' if all_detected else 'some missed ❌'}",
        "",
        "| Profile | Failure injected | Caught by | Detected | Key metric |",
        "|---------|------------------|-----------|----------|------------|",
    ]
    for r in rows:
        key = _key_metric(r["suite"], r["metrics"])
        lines.append(
            f"| `{r['profile']}` | {r['why']} | `{r['suite']}` | "
            f"{'yes' if r['detected'] else 'NO'} | {key} |"
        )
    lines.append("")
    (DOCS_DIR / "demo-failures.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _key_metric(suite: str, m: dict) -> str:
    if suite == "consistency":
        return f"mean_agreement={m['mean_agreement']}"
    if suite == "golden_accuracy":
        return f"accuracy={m['accuracy']}"
    if suite == "prompt_injection":
        return f"hijacked={m['hijacked']}/{m['n']}"
    if suite == "schema_contract":
        return f"parse_failures={m['parse_failures']}"
    return json.dumps(m)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="llmqa", description="QA harness for LLM outputs")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("run", help="run all suites and write reports")
    pr.add_argument("--provider", default="mock", choices=["mock", "anthropic", "local"])
    pr.add_argument("--profile", default="good")
    pr.add_argument("--seed", type=int, default=1234)
    pr.set_defaults(func=cmd_run)

    pc = sub.add_parser("compare", help="regression gate vs a baseline")
    pc.add_argument("--baseline", default=str(BASELINES_DIR / "baseline.json"))
    pc.add_argument("--current", default=str(REPORTS_DIR / "latest.json"))
    pc.set_defaults(func=cmd_compare)

    pd = sub.add_parser("demo-failures", help="prove the harness detects injected failures")
    pd.add_argument("--seed", type=int, default=1234)
    pd.set_defaults(func=cmd_demo_failures)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
