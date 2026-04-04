from __future__ import annotations

from app.application.positions.dto import ReadingPositionDTO
from app.domain.positions.models import ReadingPosition
from app.domain.positions.repositories import ReadingPositionRepository


class ReadingPositionService:
    def __init__(self, positions: ReadingPositionRepository) -> None:
        self._positions = positions

    def save(self, user_id: str, book_id: str, position_cfi: str, position_char: int) -> None:
        self._positions.save(
            ReadingPosition(
                user_id=user_id,
                book_id=book_id,
                position_cfi=position_cfi,
                position_char=position_char,
            )
        )

    def get(self, user_id: str, book_id: str) -> ReadingPositionDTO | None:
        position = self._positions.get(user_id, book_id)
        if not position:
            return None
        return ReadingPositionDTO(
            book_id=position.book_id,
            user_id=position.user_id,
            position_cfi=position.position_cfi,
            position_char=position.position_char,
            updated_at=position.updated_at,
        )
