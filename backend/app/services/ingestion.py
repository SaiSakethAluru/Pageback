from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from supabase import Client, create_client

from app.services.llm.provider_factory import get_provider
from app.utils import parser_factory, token_counter
from config import Config

logger = logging.getLogger(__name__)

BOOKS_TABLE = "books"
BOOK_CHUNKS_TABLE = "book_chunks"
BOOKS_BUCKET = "books"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


def ingest_book(book_id: str, user_id: str, storage_path: str) -> None:
    filepath = ""
    try:
        _update_status(
            book_id,
            status="processing",
            step="queued",
            progress=0,
            error=None,
        )
        filepath = _download_file(storage_path)
        _update_status(book_id, status="processing", step="downloaded", progress=10, error=None)
        chapters = _extract_text(filepath)
        _update_status(book_id, status="processing", step="parsed", progress=20, error=None)
        chunks = _chunk_text(chapters)
        _update_status(book_id, status="processing", step=f"chunked ({len(chunks)} chunks)", progress=35, error=None)
        embedded_chunks = _embed_chunks(book_id=book_id, chunks=chunks)
        _store_chunks(book_id, embedded_chunks)
        _update_status(book_id, status="complete", step="done", progress=100, error=None)
    except Exception as e:
        logger.exception("Failed ingestion pipeline for book_id=%s user_id=%s", book_id, user_id)
        _update_status(book_id, status="failed", step=None, progress=None, error="Ingestion failed. See server logs.")
        # Also store the message for UI/debugging.
        try:
            msg = str(e)[:2000]
            if msg:
                _update_status(book_id, status="failed", step=None, progress=None, error=msg)
        except Exception:
            pass
        raise
    finally:
        if filepath:
            Path(filepath).unlink(missing_ok=True)


def _download_file(storage_path: str) -> str:
    content = _supabase().storage.from_(BOOKS_BUCKET).download(storage_path)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
        temp_file.write(content)
        return temp_file.name


def _extract_text(filepath: str) -> list[dict]:
    return parser_factory.get_parser(filepath).extract()


def _chunk_text(chapters: list[dict]) -> list[dict]:
    chunks: list[dict] = []
    global_char_offset = 0

    for chapter in chapters:
        chapter_index = int(chapter["chapter_index"])
        text = str(chapter["text"])
        start_index = 0
        chunk_index = 0

        while start_index < len(text):
            end_index = min(len(text), start_index + 2000)
            chunk_text = text[start_index:end_index]

            while (
                end_index < len(text)
                and token_counter.count(chunk_text) < Config.CHUNK_SIZE_TOKENS
                and end_index < start_index + 4000
            ):
                end_index += 200
                chunk_text = text[start_index:min(len(text), end_index)]

            while token_counter.count(chunk_text) > Config.CHUNK_SIZE_TOKENS and len(chunk_text) > 1:
                end_index -= 50
                chunk_text = text[start_index:end_index]

            token_count = token_counter.count(chunk_text)
            chunk_start = global_char_offset + start_index
            chunk_end = global_char_offset + end_index

            chunks.append(
                {
                    "chapter_index": chapter_index,
                    "chunk_index": chunk_index,
                    "start_char": chunk_start,
                    "end_char": chunk_end,
                    "token_count": token_count,
                    "text": chunk_text,
                }
            )

            chunk_index += 1
            if end_index >= len(text):
                break

            overlap_chars = min(Config.CHUNK_OVERLAP_TOKENS * 4, max(1, end_index - start_index - 1))
            start_index = max(start_index + 1, end_index - overlap_chars)

        global_char_offset += len(text) + 2

    return chunks


def _embed_chunks(book_id: str, chunks: list[dict]) -> list[dict]:
    provider = get_provider()
    total = len(chunks)
    # Note: provider.embed_batch is implemented for providers that support batching.
    for start in range(0, total, 100):
        batch = chunks[start : start + 100]
        # Best-effort progress update; if columns don't exist in your schema yet
        # this will silently fall back to updating `ingestion_status` only.
        _update_status(
            book_id=book_id,
            status="processing",
            step=f"embedding ({start}/{total})",
            progress=35 + int(60 * (min(start + len(batch), total) / max(total, 1))),
            error=None,
        )
        embeddings = provider.embed_batch([chunk["text"] for chunk in batch])
        for chunk, embedding in zip(batch, embeddings):
            chunk["embedding"] = embedding
    return chunks


def _store_chunks(book_id: str, chunks: list[dict]) -> None:
    if not chunks:
        return

    rows = []
    for chunk in chunks:
        rows.append(
            {
                "book_id": book_id,
                "chapter_index": chunk["chapter_index"],
                "chunk_index": chunk["chunk_index"],
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "token_count": chunk["token_count"],
                "text": chunk["text"],
                "embedding": chunk["embedding"],
            }
        )

    _supabase().table(BOOK_CHUNKS_TABLE).insert(rows).execute()


def _update_status(
    book_id: str,
    status: str,
    step: str | None = None,
    progress: int | None = None,
    error: str | None = None,
) -> None:
    # Always update `ingestion_status` (this column is required by existing code/tests).
    _supabase().table(BOOKS_TABLE).update({"ingestion_status": status}).eq("id", book_id).execute()

    # Optionally update richer progress columns if they exist in the schema.
    extra: dict[str, object] = {}
    if step is not None:
        extra["ingestion_step"] = step
    if progress is not None:
        extra["ingestion_progress"] = progress
    if error is not None:
        extra["ingestion_error"] = error

    if not extra:
        return

    try:
        _supabase().table(BOOKS_TABLE).update(extra).eq("id", book_id).execute()
    except Exception:
        # If the schema hasn't been migrated yet, keep ingestion working.
        logger.debug("Progress columns may not exist; skipping extra update for book_id=%s", book_id)
