from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo, IngestionRequest


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
    def create_ingestion_request(self, request: IngestionRequest) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_ingestion_request(self, request_id: str, ingestion: IngestionInfo) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_ingestion_request_started(self, request_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def mark_ingestion_request_finished(
        self,
        request_id: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_ingestion_request_task_id(self, request_id: str, task_id: str | None) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_latest_ingestion_request(self, book_id: str, user_id: str) -> IngestionRequest | None:
        raise NotImplementedError

    @abstractmethod
    def get_ingestion_request(self, request_id: str) -> IngestionRequest | None:
        raise NotImplementedError

    @abstractmethod
    def list_ingestion_requests_by_user(self, user_id: str, statuses: list[str] | None = None) -> list[IngestionRequest]:
        raise NotImplementedError

    @abstractmethod
    def update_ingestion_request_progress(
        self,
        request_id: str,
        embedded_chunks: int,
        total_chunks: int,
        embedded_tokens: int,
        total_tokens: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def update_ingestion_request_control(self, request_id: str, control_status: str, status: str | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def ensure_model_config(self, provider: str, recap_model: str, embedding_model: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete(self, book_id: str, user_id: str) -> None:
        raise NotImplementedError


class ChunkRepository(ABC):
    @abstractmethod
    def delete_by_book(self, book_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def replace_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upsert_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_embedded_keys(self, book_id: str) -> set[tuple[int, int]]:
        raise NotImplementedError

    @abstractmethod
    def find_before_position(self, book_id: str, position_char: int) -> list[BookChunk]:
        raise NotImplementedError

    @abstractmethod
    def search_similar(
        self,
        book_id: str,
        query_embedding: list[float],
        max_char_offset: int,
        token_budget: int,
    ) -> list[BookChunk]:
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
