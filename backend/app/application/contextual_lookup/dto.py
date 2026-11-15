from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextualLookupRequestDTO:
    book_id: str
    term: str
    position_char: int = 0
    position_cfi: str | None = None


@dataclass(frozen=True)
class ContextualLookupResultDTO:
    term: str
    explanation: str
    grounded: bool
