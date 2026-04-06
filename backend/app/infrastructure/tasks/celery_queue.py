from __future__ import annotations

from app.domain.books.queue import BookIngestionQueue
from app.tasks.ingestion_tasks import ingest_book_task


class CeleryBookIngestionQueue(BookIngestionQueue):
    def enqueue(self, book_id: str, user_id: str, storage_path: str) -> str | None:
        task = ingest_book_task.delay(book_id, user_id, storage_path)
        return task.id
