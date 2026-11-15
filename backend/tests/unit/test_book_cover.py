import pytest
from unittest.mock import MagicMock

from app.application.books.service import BookService
from app.domain.books.models import Book, BookMetadata, IngestionInfo


class FakeBookRepo:
    def __init__(self, books=None):
        self._books = {b.id: b for b in (books or [])}
        self.updated_covers = {}

    def get_by_id(self, book_id: str, user_id: str):
        book = self._books.get(book_id)
        if book and book.user_id == user_id:
            return book
        return None

    def update_cover_path(self, book_id: str, cover_path: str):
        self.updated_covers[book_id] = cover_path
        if book_id in self._books:
            b = self._books[book_id]
            self._books[book_id] = Book(
                id=b.id,
                user_id=b.user_id,
                storage_path=b.storage_path,
                metadata=b.metadata,
                ingestion=b.ingestion,
                cover_path=cover_path,
                created_at=b.created_at,
            )


class FakeStorage:
    def __init__(self):
        self.uploaded = []

    def upload(self, path: str, content: bytes, content_type: str):
        self.uploaded.append((path, content, content_type))

    def create_signed_url(self, path: str, expires_in_seconds: int = 86400):
        return f"signed_url_for_{path}"


def test_update_book_cover_success():
    book = Book(
        id="b1",
        user_id="u1",
        storage_path="u1/b1/original.epub",
        metadata=BookMetadata(title="Dune", author="Frank Herbert"),
        ingestion=IngestionInfo(status="ready"),
    )
    repo = FakeBookRepo([book])
    storage = FakeStorage()

    service = BookService(
        books=repo,
        storage=storage,
        chunks=MagicMock(),
        positions=MagicMock(),
    )

    signed_url = service.update_book_cover(
        book_id="b1",
        user_id="u1",
        file_bytes=b"fake_image_bytes",
        content_type="image/jpeg",
    )

    assert signed_url == "signed_url_for_u1/b1/cover.jpg"
    assert repo.updated_covers["b1"] == "u1/b1/cover.jpg"
    assert len(storage.uploaded) == 1
    assert storage.uploaded[0][0] == "u1/b1/cover.jpg"


def test_update_book_cover_not_found():
    repo = FakeBookRepo([])
    storage = FakeStorage()

    service = BookService(
        books=repo,
        storage=storage,
        chunks=MagicMock(),
        positions=MagicMock(),
    )

    signed_url = service.update_book_cover(
        book_id="nonexistent",
        user_id="u1",
        file_bytes=b"fake_image_bytes",
    )

    assert signed_url is None
