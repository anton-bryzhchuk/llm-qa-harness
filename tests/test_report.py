"""Unit tests for report rendering and the full-run assembly."""
from __future__ import annotations

from llmqa.harness import run_all
from llmqa.report import render_markdown, write_reports


def test_run_all_structure():
    report = run_all(profile="good")
    assert report["passed"] is True
    names = {s["name"] for s in report["suites"]}
    assert names == {
        "schema_contract",
        "golden_accuracy",
        "consistency",
        "invariance",
        "prompt_injection",
    }
    assert report["operational"]["simulated"] is True
    assert report["operational"]["n_calls"] == 40


def test_markdown_renders(tmp_path):
    report = run_all(profile="good")
    md = render_markdown(report)
    assert "# LLM QA Harness" in md
    assert "Operational metrics" in md
    assert "How to read this" in md
    json_path, md_path = write_reports(report, tmp_path)
    assert json_path.exists() and md_path.exists()
    assert md_path.read_text(encoding="utf-8").startswith("# LLM QA Harness")


def test_run_all_deterministic():
    a = run_all(profile="good")
    b = run_all(profile="good")
    # drop the timestamp before comparing
    a["meta"].pop("generated_at")
    b["meta"].pop("generated_at")
    assert a == b
