from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.positions.models import ReadingPosition


class ReadingPositionRepository(ABC):
    @abstractmethod
    def save(self, position: ReadingPosition) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, user_id: str, book_id: str) -> ReadingPosition | None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, user_id: str, book_id: str) -> None:
        raise NotImplementedError
