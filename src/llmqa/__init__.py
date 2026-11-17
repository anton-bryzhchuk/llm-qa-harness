"""llmqa: a pytest-based QA harness for LLM outputs.

Exposes the core types used across the test suites and CLI.
"""
from __future__ import annotations

from .classify import ClassifyResult, classify_ticket
from .models import Category, Classification, Priority

__all__ = [
    "Category",
    "Priority",
    "Classification",
    "ClassifyResult",
    "classify_ticket",
]

__version__ = "0.1.0"
