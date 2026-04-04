from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from app.domain.books.models import BookChunk
from app.domain.books.repositories import BookRepository, BookStorage, ChunkRepository
from app.domain.recap.models import LLMGateway
from app.utils import parser_factory, token_counter
from config import Config

logger = logging.getLogger(__name__)


class BookIngestionService:
    def __init__(
        self,
        books: BookRepository,
        storage: BookStorage,
        chunks: ChunkRepository,
        llm: LLMGateway,
    ) -> None:
        self._books = books
        self._storage = storage
        self._chunks = chunks
        self._llm = llm

    def ingest_book(self, book_id: str, user_id: str, storage_path: str) -> None:
        filepath = ""
        try:
            self._books.update_ingestion(book_id, self._ingestion(status="processing", step="queued", progress=0))
            filepath = self._download_file(storage_path)
            self._books.update_ingestion(book_id, self._ingestion(status="processing", step="downloaded", progress=10))
            chapters = parser_factory.get_parser(filepath).extract()
            self._books.update_ingestion(book_id, self._ingestion(status="processing", step="parsed", progress=20))
            chunks = self._chunk_text(book_id, chapters)
            self._books.update_ingestion(
                book_id,
                self._ingestion(status="processing", step=f"chunked ({len(chunks)} chunks)", progress=35),
            )
            embedded_chunks = self._embed_chunks(book_id, chunks)
            self._chunks.replace_for_book(book_id, embedded_chunks)
            self._books.update_ingestion(book_id, self._ingestion(status="complete", step="done", progress=100))
        except Exception as exc:
            logger.exception("Failed ingestion pipeline for book_id=%s user_id=%s", book_id, user_id)
            self._books.update_ingestion(
                book_id,
                self._ingestion(status="failed", error="Ingestion failed. See server logs."),
            )
            message = str(exc)[:2000]
            if message:
                self._books.update_ingestion(book_id, self._ingestion(status="failed", error=message))
            raise
        finally:
            if filepath:
                Path(filepath).unlink(missing_ok=True)

    def _download_file(self, storage_path: str) -> str:
        content = self._storage.download(storage_path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
            temp_file.write(content)
            return temp_file.name

    def _chunk_text(self, book_id: str, chapters: list[dict]) -> list[BookChunk]:
        chunks: list[BookChunk] = []
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
                    BookChunk(
                        book_id=book_id,
                        chapter_index=chapter_index,
                        chunk_index=chunk_index,
                        start_char=chunk_start,
                        end_char=chunk_end,
                        token_count=token_count,
                        text=chunk_text,
                    )
                )

                chunk_index += 1
                if end_index >= len(text):
                    break

                overlap_chars = min(Config.CHUNK_OVERLAP_TOKENS * 4, max(1, end_index - start_index - 1))
                start_index = max(start_index + 1, end_index - overlap_chars)

            global_char_offset += len(text) + 2

        return chunks

    def _embed_chunks(self, book_id: str, chunks: list[BookChunk]) -> list[BookChunk]:
        embedded_chunks: list[BookChunk] = []
        total = len(chunks)
        for start in range(0, total, 100):
            batch = chunks[start : start + 100]
            self._books.update_ingestion(
                book_id,
                self._ingestion(
                    status="processing",
                    step=f"embedding ({start}/{total})",
                    progress=35 + int(60 * (min(start + len(batch), total) / max(total, 1))),
                ),
            )
            embeddings = self._llm.embed_batch([chunk.text for chunk in batch])
            for chunk, embedding in zip(batch, embeddings):
                embedded_chunks.append(
                    BookChunk(
                        book_id=chunk.book_id,
                        chapter_index=chunk.chapter_index,
                        chunk_index=chunk.chunk_index,
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        token_count=chunk.token_count,
                        text=chunk.text,
                        embedding=embedding,
                    )
                )
        return embedded_chunks

    @staticmethod
    def _ingestion(
        status: str,
        step: str | None = None,
        progress: int | None = None,
        error: str | None = None,
    ):
        from app.domain.books.models import IngestionInfo

        return IngestionInfo(status=status, progress=progress, step=step, error=error)
