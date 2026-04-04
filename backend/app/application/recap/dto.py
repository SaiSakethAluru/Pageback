from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecapResultDTO:
    summary: str
    level: int
    cached: bool
