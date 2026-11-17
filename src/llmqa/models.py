"""Pydantic models describing the contract of ``classify_ticket``.

These are the single source of truth for what a valid classifier output
looks like. Every provider's raw text must parse into ``Classification`` or
it is treated as a contract violation.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Category(StrEnum):
    billing = "billing"
    technical_issue = "technical_issue"
    account_access = "account_access"
    feature_request = "feature_request"
    other = "other"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class Classification(BaseModel):
    """The structured result the LLM is contracted to return."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    category: Category
    priority: Priority
    summary: str = Field(min_length=1, max_length=200)
    language: Literal["en", "de"]
