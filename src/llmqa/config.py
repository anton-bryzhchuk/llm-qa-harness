"""Paths, thresholds and pricing constants used across the harness."""
from __future__ import annotations

import os
from pathlib import Path

# Repo layout (this file lives at src/llmqa/config.py).
PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parents[1]

PROMPTS_DIR = REPO_ROOT / "prompts"
DATA_DIR = REPO_ROOT / "data"
REPORTS_DIR = REPO_ROOT / "reports"
BASELINES_DIR = REPO_ROOT / "baselines"
DOCS_DIR = REPO_ROOT / "docs"

DEFAULT_PROMPT = PROMPTS_DIR / "classify_v1.txt"
GOLDEN_PATH = DATA_DIR / "golden.yaml"

# Thresholds (the harness's acceptance criteria).
ACCURACY_THRESHOLD = 0.85          # good profile must reach this on the golden set
CONSISTENCY_THRESHOLD = 0.80       # min agreement rate across repeated runs
CONSISTENCY_RUNS = 5               # N repeats per ticket
CONSISTENCY_SAMPLE = 10            # how many tickets to test for consistency

# Regression gate tolerances (in the same units the metrics are reported).
ACCURACY_DROP_LIMIT = 0.05         # fail if accuracy drops > 5 percentage points
CONSISTENCY_DROP_LIMIT = 0.10      # fail if consistency drops > 10 points

# Retry policy for invalid JSON.
MAX_RETRIES = 2                    # => up to 3 attempts total

# Default live model (Anthropic provider).
DEFAULT_MODEL = os.environ.get("LLM_MODEL") or "claude-haiku-4-5-20251001"

# Local OpenAI-compatible endpoint (e.g. Ollama). No API key required.
LOCAL_DEFAULT_MODEL = "llama3.2:3b"


def llm_base_url() -> str:
    return os.environ.get("LLM_BASE_URL", "").strip() or "http://localhost:11434/v1"


def local_model() -> str:
    return os.environ.get("LLM_MODEL", "").strip() or LOCAL_DEFAULT_MODEL

# Approximate Anthropic Haiku pricing (USD per 1M tokens). Used for the
# simulated/estimated cost line. These are rounded public list figures and are
# only an estimate, not a billing source of truth.
PRICE_INPUT_PER_MTOK = 1.00
PRICE_OUTPUT_PER_MTOK = 5.00


def anthropic_api_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    return key or None
