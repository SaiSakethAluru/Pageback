from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone

from supabase import Client

from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo, IngestionRequest
from app.domain.books.repositories import BookRepository, ChunkRepository

logger = logging.getLogger(__name__)

BOOKS_TABLE = "books"
BOOK_CHUNKS_TABLE = "book_chunks"
INGESTION_REQUESTS_TABLE = "ingestion_requests"
INGESTION_REQUEST_EVENTS_TABLE = "ingestion_request_events"
AI_MODEL_CONFIGS_TABLE = "ai_model_configs"


def _map_book(row: dict) -> Book:
    return Book(
        id=str(row.get("id")),
        user_id=str(row.get("user_id")),
        storage_path=str(row.get("storage_path")),
        metadata=BookMetadata(
            title=row.get("title"),
            author=row.get("author"),
        ),
        ingestion=IngestionInfo(
            status=str(row.get("ingestion_status") or "ready"),
            progress=row.get("ingestion_progress"),
            step=row.get("ingestion_step"),
            error=row.get("ingestion_error"),
            request_id=row.get("ingestion_request_id"),
        ),
        cover_path=row.get("cover_path"),
        created_at=row.get("created_at"),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SupabaseBookRepository(BookRepository):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def create(self, book: Book) -> None:
        self._client().table(BOOKS_TABLE).insert(
            {
                "id": book.id,
                "user_id": book.user_id,
                "storage_path": book.storage_path,
                "title": book.metadata.title,
                "author": book.metadata.author,
                "ingestion_status": book.ingestion.status,
            }
        ).execute()

    def get_by_id(self, book_id: str, user_id: str) -> Book | None:
        response = (
            self._select_books()
            .eq("id", book_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return _map_book(rows[0])

    def list_by_user(self, user_id: str) -> list[Book]:
        response = self._select_books().eq("user_id", user_id).order("created_at", desc=True).execute()
        return [_map_book(row) for row in (response.data or [])]

    def update_metadata(self, book_id: str, user_id: str, metadata: BookMetadata) -> Book | None:
        response = (
            self._client()
            .table(BOOKS_TABLE)
            .update({"title": metadata.title, "author": metadata.author})
            .eq("id", book_id)
            .eq("user_id", user_id)
            .execute()
        )
        rows = response.data or []
        if rows:
            return _map_book({**rows[0], "user_id": user_id})
        return self.get_by_id(book_id, user_id)

    def update_cover_path(self, book_id: str, cover_path: str) -> None:
        try:
            self._client().table(BOOKS_TABLE).update({"cover_path": cover_path}).eq("id", book_id).execute()
        except Exception:
            logger.debug("cover_path column missing; skipping cover_path update for book_id=%s", book_id)

    def update_ingestion(self, book_id: str, ingestion: IngestionInfo) -> None:
        extra: dict[str, object] = {
            "ingestion_status": ingestion.status,
            "ingestion_progress": ingestion.progress,
            "ingestion_step": ingestion.step,
            "ingestion_error": ingestion.error,
            "ingestion_request_id": ingestion.request_id,
        }
        try:
            self._client().table(BOOKS_TABLE).update(extra).eq("id", book_id).execute()
        except Exception:
            extra.pop("ingestion_request_id", None)
            try:
                self._client().table(BOOKS_TABLE).update(extra).eq("id", book_id).execute()
            except Exception:
                logger.debug("Progress columns may not exist; skipping extra update for book_id=%s", book_id)

    def create_ingestion_request(self, request: IngestionRequest) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).insert(
            {
                "id": request.id,
                "book_id": request.book_id,
                "user_id": request.user_id,
                "book_title": request.book_title,
                "model_config_id": request.model_config_id,
                "status": request.status,
                "progress": request.progress,
                "step": request.step,
                "error_type": request.error_type,
                "error_message": request.error_message,
                "log_path": request.log_path,
                "celery_task_id": request.celery_task_id,
                "control_status": request.control_status,
                "embedded_chunks": request.embedded_chunks,
                "total_chunks": request.total_chunks,
                "embedded_tokens": request.embedded_tokens,
                "total_tokens": request.total_tokens,
            }
        ).execute()
        self._create_ingestion_event(
            request.id,
            status=request.status,
            progress=request.progress,
            step=request.step,
        )

    def update_ingestion_request(self, request_id: str, ingestion: IngestionInfo) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).update(
            {
                "status": ingestion.status,
                "progress": ingestion.progress,
                "step": ingestion.step,
                "error_message": ingestion.error,
            }
        ).eq("id", request_id).execute()
        self._create_ingestion_event(
            request_id,
            status=ingestion.status,
            progress=ingestion.progress,
            step=ingestion.step,
            message=ingestion.error,
        )

    def mark_ingestion_request_started(self, request_id: str) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).update(
            {"status": "processing", "control_status": "active", "started_at": _utc_now()}
        ).eq("id", request_id).execute()
        self._create_ingestion_event(request_id, status="processing", step="started")

    def mark_ingestion_request_finished(
        self,
        request_id: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).update(
            {
                "status": status,
                "error_type": error_type,
                "error_message": error_message,
                "control_status": "active" if status == "complete" else status,
                "completed_at": _utc_now(),
            }
        ).eq("id", request_id).execute()
        self._create_ingestion_event(
            request_id,
            status=status,
            message=error_message,
        )

    def update_ingestion_request_task_id(self, request_id: str, task_id: str | None) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).update({"celery_task_id": task_id}).eq("id", request_id).execute()

    def get_latest_ingestion_request(self, book_id: str, user_id: str) -> IngestionRequest | None:
        response = (
            self._client()
            .table(INGESTION_REQUESTS_TABLE)
            .select("*")
            .eq("book_id", book_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return self._map_ingestion_request(rows[0])

    def get_ingestion_request(self, request_id: str) -> IngestionRequest | None:
        response = (
            self._client()
            .table(INGESTION_REQUESTS_TABLE)
            .select("*")
            .eq("id", request_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return self._map_ingestion_request(rows[0])

    def list_ingestion_requests_by_user(self, user_id: str, statuses: list[str] | None = None) -> list[IngestionRequest]:
        query = (
            self._client()
            .table(INGESTION_REQUESTS_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        if statuses:
            query = query.in_("status", statuses)
        response = query.execute()
        return [self._map_ingestion_request(row) for row in (response.data or [])]

    def update_ingestion_request_progress(
        self,
        request_id: str,
        embedded_chunks: int,
        total_chunks: int,
        embedded_tokens: int,
        total_tokens: int,
    ) -> None:
        self._client().table(INGESTION_REQUESTS_TABLE).update(
            {
                "embedded_chunks": embedded_chunks,
                "total_chunks": total_chunks,
                "embedded_tokens": embedded_tokens,
                "total_tokens": total_tokens,
            }
        ).eq("id", request_id).execute()

    def update_ingestion_request_control(self, request_id: str, control_status: str, status: str | None = None) -> None:
        update: dict[str, object] = {"control_status": control_status}
        if status:
            update["status"] = status
        self._client().table(INGESTION_REQUESTS_TABLE).update(update).eq("id", request_id).execute()
        self._create_ingestion_event(request_id, status=status or control_status, step=control_status)

    def ensure_model_config(self, provider: str, recap_model: str, embedding_model: str) -> str:
        response = (
            self._client()
            .table(AI_MODEL_CONFIGS_TABLE)
            .upsert(
                {
                    "provider": provider,
                    "recap_model": recap_model,
                    "embedding_model": embedding_model,
                },
                on_conflict="provider,recap_model,embedding_model",
            )
            .execute()
        )
        rows = response.data or []
        if rows:
            return str(rows[0]["id"])

        response = (
            self._client()
            .table(AI_MODEL_CONFIGS_TABLE)
            .select("id")
            .eq("provider", provider)
            .eq("recap_model", recap_model)
            .eq("embedding_model", embedding_model)
            .limit(1)
            .execute()
        )
        return str((response.data or [])[0]["id"])

    def _create_ingestion_event(
        self,
        request_id: str,
        status: str,
        progress: int | None = None,
        step: str | None = None,
        message: str | None = None,
    ) -> None:
        self._client().table(INGESTION_REQUEST_EVENTS_TABLE).insert(
            {
                "request_id": request_id,
                "status": status,
                "progress": progress,
                "step": step,
                "message": message,
            }
        ).execute()

    def delete(self, book_id: str, user_id: str) -> None:
        self._client().table(BOOKS_TABLE).delete().eq("id", book_id).eq("user_id", user_id).execute()

    def _client(self) -> Client:
        return self._client_factory()

    def _select_books(self):
        try:
            return self._client().table(BOOKS_TABLE).select(
                "id, user_id, storage_path, title, author, cover_path, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error, ingestion_request_id"
            )
        except Exception:
            try:
                return self._client().table(BOOKS_TABLE).select(
                    "id, user_id, storage_path, title, author, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error, ingestion_request_id"
                )
            except Exception:
                return self._client().table(BOOKS_TABLE).select(
                    "id, user_id, storage_path, title, author, ingestion_status, created_at"
                )

    @staticmethod
    def _map_ingestion_request(row: dict) -> IngestionRequest:
        return IngestionRequest(
            id=str(row.get("id")),
            book_id=str(row.get("book_id")),
            user_id=str(row.get("user_id")),
            book_title=row.get("book_title"),
            model_config_id=row.get("model_config_id"),
            status=str(row.get("status") or "queued"),
            progress=row.get("progress"),
            step=row.get("step"),
            error_type=row.get("error_type"),
            error_message=row.get("error_message"),
            log_path=row.get("log_path"),
            celery_task_id=row.get("celery_task_id"),
            control_status=str(row.get("control_status") or "active"),
            embedded_chunks=int(row.get("embedded_chunks") or 0),
            total_chunks=int(row["total_chunks"]) if row.get("total_chunks") is not None else None,
            embedded_tokens=int(row.get("embedded_tokens") or 0),
            total_tokens=int(row["total_tokens"]) if row.get("total_tokens") is not None else None,
            created_at=row.get("created_at"),
            started_at=row.get("started_at"),
            completed_at=row.get("completed_at"),
        )


class SupabaseChunkRepository(ChunkRepository):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def delete_by_book(self, book_id: str) -> None:
        self._client_factory().table(BOOK_CHUNKS_TABLE).delete().eq("book_id", book_id).execute()

    def replace_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        self.delete_by_book(book_id)
        if not chunks:
            return
        self.upsert_for_book(book_id, chunks)

    def upsert_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        if not chunks:
            return
        rows = [
            {
                "book_id": chunk.book_id,
                "chapter_index": chunk.chapter_index,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "token_count": chunk.token_count,
                "text": chunk.text,
                "embedding": chunk.embedding,
            }
            for chunk in chunks
        ]
        self._client_factory().table(BOOK_CHUNKS_TABLE).upsert(
            rows,
            on_conflict="book_id,chapter_index,chunk_index",
        ).execute()

    def find_embedded_keys(self, book_id: str) -> set[tuple[int, int]]:
        response = (
            self._client_factory()
            .table(BOOK_CHUNKS_TABLE)
            .select("chapter_index, chunk_index")
            .eq("book_id", book_id)
            .execute()
        )
        return {
            (int(row.get("chapter_index") or 0), int(row.get("chunk_index") or 0))
            for row in (response.data or [])
        }

    def find_before_position(self, book_id: str, position_char: int) -> list[BookChunk]:
        response = (
            self._client_factory()
            .table(BOOK_CHUNKS_TABLE)
            .select("book_id, chapter_index, chunk_index, start_char, end_char, token_count, text")
            .eq("book_id", book_id)
            .lte("start_char", position_char)
            .order("start_char", desc=True)
            .execute()
        )
        chunks = [self._map_chunk(row) for row in (response.data or [])]
        if not chunks and position_char > 0:
            earliest = (
                self._client_factory()
                .table(BOOK_CHUNKS_TABLE)
                .select("book_id, chapter_index, chunk_index, start_char, end_char, token_count, text")
                .eq("book_id", book_id)
                .order("start_char", desc=False)
                .limit(1)
                .execute()
            )
            if earliest.data and int(earliest.data[0].get("start_char", 0) or 0) <= position_char:
                chunks = [self._map_chunk(earliest.data[0])]
        return chunks

    def find_by_chapter(self, book_id: str, chapter_index: int) -> list[BookChunk]:
        response = (
            self._client_factory()
            .table(BOOK_CHUNKS_TABLE)
            .select("book_id, chapter_index, chunk_index, start_char, end_char, token_count, text")
            .eq("book_id", book_id)
            .eq("chapter_index", chapter_index)
            .order("chunk_index", desc=False)
            .execute()
        )
        return [self._map_chunk(row) for row in (response.data or [])]

    def search_similar(
        self,
        book_id: str,
        query_embedding: list[float],
        max_char_offset: int,
        token_budget: int,
    ) -> list[BookChunk]:
        response = (
            self._client_factory()
            .rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "p_book_id": book_id,
                    "max_char_offset": max_char_offset,
                    "token_budget": token_budget,
                },
            )
            .execute()
        )
        filtered = [
            row for row in (response.data or []) if int(row.get("start_char", 0) or 0) <= max_char_offset
        ]
        return [self._map_chunk(row) for row in filtered]

    @staticmethod
    def _map_chunk(row: dict) -> BookChunk:
        return BookChunk(
            book_id=str(row.get("book_id") or ""),
            chapter_index=int(row.get("chapter_index") or 0),
            chunk_index=int(row.get("chunk_index") or 0),
            start_char=int(row.get("start_char") or 0),
            end_char=int(row.get("end_char") or 0),
            token_count=int(row.get("token_count") or 0),
            text=str(row.get("text") or ""),
            embedding=row.get("embedding"),
        )
