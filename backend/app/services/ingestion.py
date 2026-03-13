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
        _update_status(book_id, "processing")
        filepath = _download_file(storage_path)
        chapters = _extract_text(filepath)
        chunks = _chunk_text(chapters)
        embedded_chunks = _embed_chunks(chunks)
        _store_chunks(book_id, embedded_chunks)
        _update_status(book_id, "complete")
    except Exception:
        logger.exception("Failed ingestion pipeline for book_id=%s user_id=%s", book_id, user_id)
        _update_status(book_id, "failed")
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


def _embed_chunks(chunks: list[dict]) -> list[dict]:
    provider = get_provider()
    for start in range(0, len(chunks), 100):
        batch = chunks[start : start + 100]
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


def _update_status(book_id: str, status: str) -> None:
    _supabase().table(BOOKS_TABLE).update({"ingestion_status": status}).eq("id", book_id).execute()
