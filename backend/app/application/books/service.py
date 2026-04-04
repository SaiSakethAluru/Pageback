from __future__ import annotations

import uuid
from dataclasses import asdict

from app.domain.books.models import Book, BookMetadata, IngestionInfo
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
    ) -> Book:
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
        return book

    def get_book(self, book_id: str, user_id: str) -> Book | None:
        return self._books.get_by_id(book_id, user_id)

    def list_books(self, user_id: str) -> list[Book]:
        return self._books.list_by_user(user_id)

    def update_metadata(self, book_id: str, user_id: str, title: str | None, author: str | None) -> Book | None:
        return self._books.update_metadata(book_id, user_id, BookMetadata(title=title, author=author))

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
    ) -> None:
        self._books.update_ingestion(
            book_id,
            IngestionInfo(
                status=status,
                progress=progress,
                step=step,
                error=error,
            ),
        )

    def create_signed_book_url(self, book_id: str, user_id: str, expires_in_seconds: int = 3600) -> str | None:
        book = self._books.get_by_id(book_id, user_id)
        if not book:
            return None
        return self._storage.create_signed_url(book.storage_path, expires_in_seconds)

    def create_signed_cover_url(self, cover_path: str | None, expires_in_seconds: int = 3600) -> str | None:
        if not cover_path:
            return None
        return self._storage.create_signed_url(cover_path, expires_in_seconds)

    def delete_book(self, book_id: str, user_id: str) -> Book | None:
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
        return book

    @staticmethod
    def serialize(book: Book, cover_url: str | None = None) -> dict:
        data = asdict(book)
        metadata = data.pop("metadata")
        ingestion = data.pop("ingestion")
        return {
            "id": data["id"],
            "title": metadata["title"],
            "author": metadata["author"],
            "cover_path": data["cover_path"],
            "cover_url": cover_url,
            "ingestion_status": ingestion["status"],
            "ingestion_progress": ingestion["progress"],
            "ingestion_step": ingestion["step"],
            "ingestion_error": ingestion["error"],
            "created_at": data["created_at"],
        }
