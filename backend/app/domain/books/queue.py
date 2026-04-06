from __future__ import annotations

from abc import ABC, abstractmethod


class BookIngestionQueue(ABC):
    @abstractmethod
    def enqueue(self, book_id: str, user_id: str, storage_path: str) -> str | None:
        raise NotImplementedError
