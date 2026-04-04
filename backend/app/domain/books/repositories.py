from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.books.models import Book, BookMetadata, IngestionInfo


class BookRepository(ABC):
    @abstractmethod
    def create(self, book: Book) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, book_id: str, user_id: str) -> Book | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_user(self, user_id: str) -> list[Book]:
        raise NotImplementedError

    @abstractmethod
    def update_metadata(self, book_id: str, user_id: str, metadata: BookMetadata) -> Book | None:
        raise NotImplementedError

    @abstractmethod
    def update_cover_path(self, book_id: str, cover_path: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_ingestion(self, book_id: str, ingestion: IngestionInfo) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, book_id: str, user_id: str) -> None:
        raise NotImplementedError


class ChunkRepository(ABC):
    @abstractmethod
    def delete_by_book(self, book_id: str) -> None:
        raise NotImplementedError


class BookStorage(ABC):
    @abstractmethod
    def upload(self, path: str, content: bytes, content_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def download(self, path: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def remove_many(self, paths: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_signed_url(self, path: str, expires_in_seconds: int) -> str | None:
        raise NotImplementedError
