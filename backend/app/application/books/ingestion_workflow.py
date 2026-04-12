from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass
from pathlib import Path

from app.application.books.dto import BookFileDTO
from app.application.books.service import BookService
from app.domain.books.models import IngestionRequest
from app.domain.books.queue import BookIngestionQueue
from app.domain.recap.models import LLMGateway
from config import Config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionStartResultDTO:
    book_id: str
    request_id: str | None
    status: str
    task_id: str | None = None


class BookIngestionWorkflow:
    def __init__(self, books: BookService, queue: BookIngestionQueue, llm: LLMGateway) -> None:
        self._books = books
        self._queue = queue
        self._llm = llm

    def start(self, book_id: str, user_id: str) -> tuple[BookFileDTO | None, IngestionStartResultDTO]:
        book = self._books.get_book(book_id, user_id)
        if not book:
            return None, IngestionStartResultDTO(book_id=book_id, request_id=None, status="missing")

        request_id = str(uuid.uuid4())
        log_path = str(Path(Config.INGESTION_LOG_DIR) / f"{request_id}.log")
        model_config_id = self._books.ensure_model_config(
            self._llm.provider_name,
            self._llm.recap_model,
            self._llm.embedding_model,
        )
        ingestion_request = IngestionRequest(
            id=request_id,
            book_id=book_id,
            user_id=user_id,
            book_title=book.title,
            model_config_id=model_config_id,
            status="queued",
            progress=0,
            step="queued",
            log_path=log_path,
        )
        self._books.create_ingestion_request(ingestion_request)
        self._books.update_ingestion_status(
            book_id,
            status="processing",
            progress=0,
            step="queued",
            error=None,
            request_id=request_id,
        )

        try:
            task_id = self._queue.enqueue(request_id, book_id, user_id, book.storage_path)
        except Exception as exc:
            error_type = type(exc).__name__
            error_message = _concise_error(exc)
            self._books.update_ingestion_status(
                book_id,
                status="failed",
                progress=0,
                step="queue failed",
                error=error_message,
                request_id=request_id,
            )
            self._books.mark_ingestion_request_finished(
                request_id,
                status="failed",
                error_type=error_type,
                error_message=error_message,
            )
            raise
        try:
            self._books.update_ingestion_request_task_id(request_id, task_id)
        except Exception:
            logger.exception("Could not persist Celery task ID for ingestion request_id=%s", request_id)
        return book, IngestionStartResultDTO(
            book_id=book_id,
            request_id=request_id,
            status="processing",
            task_id=task_id,
        )

    def resume(self, request_id: str, user_id: str) -> IngestionStartResultDTO | None:
        request = self._books.get_ingestion_request(request_id)
        if not request or request.user_id != user_id:
            return None

        book = self._books.get_book(request.book_id, user_id)
        if not book:
            return None

        self._books.update_ingestion_request_control(request_id, control_status="active", status="queued")
        self._books.update_ingestion_status(
            request.book_id,
            status="processing",
            progress=request.progress,
            step="queued",
            error=None,
            request_id=request_id,
        )
        task_id = self._queue.enqueue(request_id, request.book_id, user_id, book.storage_path)
        self._books.update_ingestion_request_task_id(request_id, task_id)
        return IngestionStartResultDTO(
            book_id=request.book_id,
            request_id=request_id,
            status="processing",
            task_id=task_id,
        )


def _concise_error(exc: Exception) -> str:
    message = str(exc).splitlines()[0] if str(exc) else ""
    if message:
        return f"{type(exc).__name__}: {message}"[:2000]
    return type(exc).__name__
