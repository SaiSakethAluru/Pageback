from __future__ import annotations

import uuid

from app.application.books.dto import BookDTO, BookFileDTO, BookStatusDTO, IngestionRequestDTO
from app.domain.books.models import Book, BookMetadata, IngestionInfo, IngestionRequest
from app.domain.books.repositories import BookRepository, BookStorage, ChunkRepository
from app.domain.positions.repositories import ReadingPositionRepository


class BookService:
    def __init__(
        self,
        books: BookRepository,
        storage: BookStorage,
        chunks: ChunkRepository,
        positions: ReadingPositionRepository,
    ) -> None:
        self._books = books
        self._storage = storage
        self._chunks = chunks
        self._positions = positions

    def create_book(
        self,
        user_id: str,
        file_bytes: bytes,
        content_type: str,
        title: str | None,
        author: str | None,
    ) -> BookFileDTO:
        book_id = str(uuid.uuid4())
        storage_path = f"{user_id}/{book_id}/original.epub"
        self._storage.upload(storage_path, file_bytes, content_type)
        book = Book(
            id=book_id,
            user_id=user_id,
            storage_path=storage_path,
            metadata=BookMetadata(title=title, author=author),
            ingestion=IngestionInfo(status="ready"),
        )
        self._books.create(book)
        return self._to_file_dto(book)

    def get_book(self, book_id: str, user_id: str) -> BookFileDTO | None:
        book = self._books.get_by_id(book_id, user_id)
        if not book:
            return None
        return self._to_file_dto(book)

    def list_books(self, user_id: str) -> list[BookFileDTO]:
        return [self._to_file_dto(book) for book in self._books.list_by_user(user_id)]

    def update_metadata(self, book_id: str, user_id: str, title: str | None, author: str | None) -> BookFileDTO | None:
        book = self._books.update_metadata(book_id, user_id, BookMetadata(title=title, author=author))
        if not book:
            return None
        return self._to_file_dto(book)

    def update_cover_path(self, book_id: str, cover_path: str) -> None:
        self._books.update_cover_path(book_id, cover_path)

    def upload_cover(self, path: str, content: bytes, content_type: str) -> None:
        self._storage.upload(path, content, content_type)

    def update_ingestion_status(
        self,
        book_id: str,
        status: str,
        progress: int | None = None,
        step: str | None = None,
        error: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self._books.update_ingestion(
            book_id,
            IngestionInfo(
                status=status,
                progress=progress,
                step=step,
                error=error,
                request_id=request_id,
            ),
        )

    def create_ingestion_request(self, request: IngestionRequest) -> None:
        self._books.create_ingestion_request(request)

    def update_ingestion_request_task_id(self, request_id: str, task_id: str | None) -> None:
        self._books.update_ingestion_request_task_id(request_id, task_id)

    def mark_ingestion_request_finished(
        self,
        request_id: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._books.mark_ingestion_request_finished(
            request_id,
            status=status,
            error_type=error_type,
            error_message=error_message,
        )

    def get_ingestion_request(self, request_id: str) -> IngestionRequest | None:
        return self._books.get_ingestion_request(request_id)

    def list_active_ingestion_requests(self, user_id: str) -> list[IngestionRequestDTO]:
        requests = self._books.list_ingestion_requests_by_user(
            user_id,
            statuses=["queued", "processing", "paused", "failed"],
        )
        return [self._to_ingestion_request_dto(request) for request in requests]

    def pause_ingestion_request(self, request_id: str, user_id: str) -> IngestionRequestDTO | None:
        request = self._books.get_ingestion_request(request_id)
        if not request or request.user_id != user_id:
            return None
        self._books.update_ingestion_request_control(request_id, control_status="paused", status="paused")
        self.update_ingestion_status(
            request.book_id,
            status="paused",
            progress=request.progress,
            step="paused",
            request_id=request_id,
        )
        updated = self._books.get_ingestion_request(request_id) or request
        return self._to_ingestion_request_dto(updated)

    def cancel_ingestion_request(self, request_id: str, user_id: str) -> IngestionRequestDTO | None:
        request = self._books.get_ingestion_request(request_id)
        if not request or request.user_id != user_id:
            return None
        self._books.update_ingestion_request_control(request_id, control_status="canceled", status="canceled")
        self._chunks.delete_by_book(request.book_id)
        self.update_ingestion_status(
            request.book_id,
            status="canceled",
            progress=0,
            step="canceled",
            error=None,
            request_id=request_id,
        )
        self._books.mark_ingestion_request_finished(request_id, status="canceled")
        updated = self._books.get_ingestion_request(request_id) or request
        return self._to_ingestion_request_dto(updated)

    def ensure_model_config(self, provider: str, recap_model: str, embedding_model: str) -> str:
        return self._books.ensure_model_config(provider, recap_model, embedding_model)

    def create_signed_book_url(self, book_id: str, user_id: str, expires_in_seconds: int = 3600) -> str | None:
        book = self._books.get_by_id(book_id, user_id)
        if not book:
            return None
        return self._storage.create_signed_url(book.storage_path, expires_in_seconds)

    def create_signed_cover_url(self, cover_path: str | None, expires_in_seconds: int = 3600) -> str | None:
        if not cover_path:
            return None
        return self._storage.create_signed_url(cover_path, expires_in_seconds)

    def delete_book(self, book_id: str, user_id: str) -> BookFileDTO | None:
        book = self._books.get_by_id(book_id, user_id)
        if not book:
            return None
        removable_paths = [book.storage_path]
        if book.cover_path:
            removable_paths.append(book.cover_path)
        self._storage.remove_many(removable_paths)
        self._chunks.delete_by_book(book_id)
        self._positions.delete(user_id, book_id)
        self._books.delete(book_id, user_id)
        return self._to_file_dto(book)

    def get_book_status(self, book_id: str, user_id: str) -> BookStatusDTO | None:
        book = self._books.get_by_id(book_id, user_id)
        if not book:
            return None
        latest_request = self._books.get_latest_ingestion_request(book_id, user_id)
        return BookStatusDTO(
            id=book.id,
            status=book.ingestion.status,
            progress=book.ingestion.progress,
            step=book.ingestion.step,
            error=book.ingestion.error,
            error_type=latest_request.error_type if latest_request else None,
            request_id=book.ingestion.request_id or (latest_request.id if latest_request else None),
            log_path=latest_request.log_path if latest_request else None,
            model_config_id=latest_request.model_config_id if latest_request else None,
        )

    @staticmethod
    def to_book_dto(book: BookFileDTO, cover_url: str | None = None) -> BookDTO:
        return BookDTO(
            id=book.id,
            title=book.title,
            author=book.author,
            cover_path=book.cover_path,
            cover_url=cover_url,
            ingestion_status=book.ingestion_status,
            ingestion_progress=book.ingestion_progress,
            ingestion_step=book.ingestion_step,
            ingestion_error=book.ingestion_error,
            created_at=book.created_at,
        )

    @staticmethod
    def _to_file_dto(book: Book) -> BookFileDTO:
        return BookFileDTO(
            id=book.id,
            user_id=book.user_id,
            storage_path=book.storage_path,
            title=book.metadata.title,
            author=book.metadata.author,
            cover_path=book.cover_path,
            ingestion_status=book.ingestion.status,
            ingestion_progress=book.ingestion.progress,
            ingestion_step=book.ingestion.step,
            ingestion_error=book.ingestion.error,
            created_at=book.created_at,
        )

    @staticmethod
    def _to_ingestion_request_dto(request: IngestionRequest) -> IngestionRequestDTO:
        return IngestionRequestDTO(
            id=request.id,
            book_id=request.book_id,
            book_title=request.book_title,
            status=request.status,
            control_status=request.control_status,
            progress=request.progress,
            step=request.step,
            error_type=request.error_type,
            error_message=request.error_message,
            embedded_chunks=request.embedded_chunks,
            total_chunks=request.total_chunks,
            embedded_tokens=request.embedded_tokens,
            total_tokens=request.total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )
