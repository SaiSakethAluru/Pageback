from __future__ import annotations

from dataclasses import dataclass

from app.application.books.dto import BookFileDTO
from app.application.books.service import BookService
from app.domain.books.queue import BookIngestionQueue


@dataclass(frozen=True)
class IngestionStartResultDTO:
    book_id: str
    status: str
    task_id: str | None = None


class BookIngestionWorkflow:
    def __init__(self, books: BookService, queue: BookIngestionQueue) -> None:
        self._books = books
        self._queue = queue

    def start(self, book_id: str, user_id: str) -> tuple[BookFileDTO | None, IngestionStartResultDTO]:
        book = self._books.get_book(book_id, user_id)
        if not book:
            return None, IngestionStartResultDTO(book_id=book_id, status="missing")

        self._books.update_ingestion_status(
            book_id,
            status="processing",
            progress=0,
            step="queued",
            error=None,
        )

        task_id = self._queue.enqueue(book_id, user_id, book.storage_path)
        return book, IngestionStartResultDTO(book_id=book_id, status="processing", task_id=task_id)
