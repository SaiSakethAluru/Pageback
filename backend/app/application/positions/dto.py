from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadingPositionDTO:
    book_id: str
    user_id: str
    position_cfi: str
    position_char: int
    updated_at: str | None
