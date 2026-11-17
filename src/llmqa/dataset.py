"""Loading the golden dataset and the injection test set."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .config import DATA_DIR, GOLDEN_PATH


@dataclass(frozen=True)
class GoldenTicket:
    id: str
    lang: str
    text: str
    category: str
    priority: str


@dataclass(frozen=True)
class InjectionTicket:
    id: str
    text: str
    injected_category: str  # the hijack target the injection tries to force
    true_category: str      # the category the real content should map to
    note: str


def load_golden(path: Path = GOLDEN_PATH) -> list[GoldenTicket]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [GoldenTicket(**row) for row in raw]


def load_injection(path: Path | None = None) -> list[InjectionTicket]:
    path = path or (DATA_DIR / "injection.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [InjectionTicket(**row) for row in raw]
