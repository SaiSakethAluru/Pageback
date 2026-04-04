from __future__ import annotations

import logging
from collections.abc import Callable

from supabase import Client

from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo
from app.domain.books.repositories import BookRepository, ChunkRepository

logger = logging.getLogger(__name__)

BOOKS_TABLE = "books"
BOOK_CHUNKS_TABLE = "book_chunks"


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
        ),
        cover_path=row.get("cover_path"),
        created_at=row.get("created_at"),
    )


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
        self._client().table(BOOKS_TABLE).update({"ingestion_status": ingestion.status}).eq("id", book_id).execute()
        extra: dict[str, object] = {}
        if ingestion.step is not None:
            extra["ingestion_step"] = ingestion.step
        if ingestion.progress is not None:
            extra["ingestion_progress"] = ingestion.progress
        if ingestion.error is not None:
            extra["ingestion_error"] = ingestion.error
        if not extra:
            return
        try:
            self._client().table(BOOKS_TABLE).update(extra).eq("id", book_id).execute()
        except Exception:
            logger.debug("Progress columns may not exist; skipping extra update for book_id=%s", book_id)

    def delete(self, book_id: str, user_id: str) -> None:
        self._client().table(BOOKS_TABLE).delete().eq("id", book_id).eq("user_id", user_id).execute()

    def _client(self) -> Client:
        return self._client_factory()

    def _select_books(self):
        try:
            return self._client().table(BOOKS_TABLE).select(
                "id, user_id, storage_path, title, author, cover_path, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error"
            )
        except Exception:
            try:
                return self._client().table(BOOKS_TABLE).select(
                    "id, user_id, storage_path, title, author, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error"
                )
            except Exception:
                return self._client().table(BOOKS_TABLE).select(
                    "id, user_id, storage_path, title, author, ingestion_status, created_at"
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
        self._client_factory().table(BOOK_CHUNKS_TABLE).insert(rows).execute()

    def find_before_position(self, book_id: str, position_char: int) -> list[BookChunk]:
        response = (
            self._client_factory()
            .table(BOOK_CHUNKS_TABLE)
            .select("book_id, chapter_index, chunk_index, start_char, end_char, token_count, text")
            .eq("book_id", book_id)
            .lte("end_char", position_char)
            .order("end_char", desc=True)
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
            row for row in (response.data or []) if int(row.get("end_char", 0) or 0) <= max_char_offset
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
