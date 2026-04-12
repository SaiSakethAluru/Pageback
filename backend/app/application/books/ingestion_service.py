from __future__ import annotations

import logging
import random
import time
import tempfile
from pathlib import Path

from app.domain.books.models import BookChunk
from app.domain.books.parsing import ParserFactory
from app.domain.books.repositories import BookRepository, BookStorage, ChunkRepository
from app.domain.recap.models import LLMGateway
from app.utils import token_counter
from config import Config

logger = logging.getLogger(__name__)


class BookIngestionService:
    def __init__(
        self,
        books: BookRepository,
        storage: BookStorage,
        chunks: ChunkRepository,
        llm: LLMGateway,
        parsers: ParserFactory,
    ) -> None:
        self._books = books
        self._storage = storage
        self._chunks = chunks
        self._llm = llm
        self._parsers = parsers

    def ingest_book(self, book_id: str, user_id: str, storage_path: str, request_id: str | None = None) -> None:
        filepath = ""
        try:
            if request_id:
                self._books.mark_ingestion_request_started(request_id)
            self._update_ingestion(book_id, request_id, status="processing", step="queued", progress=0)
            request = self._books.get_ingestion_request(request_id) if request_id else None
            if request_id and request and request.embedded_chunks == 0:
                self._chunks.delete_by_book(book_id)
            filepath = self._download_file(storage_path)
            self._update_ingestion(book_id, request_id, status="processing", step="downloaded", progress=10)
            chapters = self._parsers.get_parser(filepath).extract()
            self._update_ingestion(book_id, request_id, status="processing", step="parsed", progress=20)
            chunks = self._chunk_text(book_id, chapters)
            self._update_ingestion(
                book_id,
                request_id,
                status="processing",
                step=f"chunked ({len(chunks)} chunks)",
                progress=35,
            )
            self._embed_chunks(request_id, book_id, chunks)
            if self._is_control_status(request_id, "paused"):
                paused_request = self._books.get_ingestion_request(request_id) if request_id else None
                self._update_ingestion(
                    book_id,
                    request_id,
                    status="paused",
                    step="paused",
                    progress=paused_request.progress if paused_request else None,
                )
                return
            if self._is_control_status(request_id, "canceled"):
                self._chunks.delete_by_book(book_id)
                self._update_ingestion(book_id, request_id, status="canceled", step="canceled", progress=0)
                if request_id:
                    self._books.mark_ingestion_request_finished(request_id, status="canceled")
                return
            self._update_ingestion(book_id, request_id, status="complete", step="done", progress=100)
            if request_id:
                self._books.mark_ingestion_request_finished(request_id, status="complete")
        except Exception as exc:
            error_type = type(exc).__name__
            error_message = _concise_error(exc)
            logger.exception(
                "Failed ingestion pipeline request_id=%s book_id=%s user_id=%s",
                request_id,
                book_id,
                user_id,
            )
            self._update_ingestion(
                book_id,
                request_id,
                status="failed",
                error=error_message,
            )
            if request_id:
                self._books.mark_ingestion_request_finished(
                    request_id,
                    status="failed",
                    error_type=error_type,
                    error_message=error_message,
                )
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

    def _embed_chunks(self, request_id: str | None, book_id: str, chunks: list[BookChunk]) -> list[BookChunk]:
        embedded_chunks: list[BookChunk] = []
        total = len(chunks)
        total_tokens = sum(chunk.token_count for chunk in chunks)
        already_embedded = self._chunks.find_embedded_keys(book_id)
        embedded_count = sum(
            1
            for chunk in chunks
            if (chunk.chapter_index, chunk.chunk_index) in already_embedded
        )
        embedded_tokens = sum(
            chunk.token_count
            for chunk in chunks
            if (chunk.chapter_index, chunk.chunk_index) in already_embedded
        )
        self._update_embedding_progress(request_id, embedded_count, total, embedded_tokens, total_tokens)
        batches = self._embedding_batches(
            [chunk for chunk in chunks if (chunk.chapter_index, chunk.chunk_index) not in already_embedded]
        )
        for batch_index, batch in enumerate(batches):
            control_status = self._get_control_status(request_id)
            if control_status == "paused":
                return embedded_chunks
            if control_status == "canceled":
                return embedded_chunks

            embeddings = self._llm.embed_batch([chunk.text for chunk in batch])
            if len(embeddings) != len(batch):
                raise RuntimeError(
                    f"Embedding provider returned {len(embeddings)} embeddings for {len(batch)} chunks"
                )
            if self._get_control_status(request_id) == "canceled":
                self._chunks.delete_by_book(book_id)
                return embedded_chunks
            batch_embedded_chunks: list[BookChunk] = []
            for chunk, embedding in zip(batch, embeddings):
                embedded_chunk = (
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
                embedded_chunks.append(embedded_chunk)
                batch_embedded_chunks.append(embedded_chunk)
            self._chunks.upsert_for_book(book_id, batch_embedded_chunks)
            embedded_count += len(batch_embedded_chunks)
            embedded_tokens += sum(chunk.token_count for chunk in batch_embedded_chunks)
            self._update_embedding_progress(request_id, embedded_count, total, embedded_tokens, total_tokens)
            completed = min(embedded_count, total)
            self._update_ingestion(
                book_id,
                request_id,
                status="processing",
                step=f"embedding ({completed}/{total})",
                progress=35 + int(60 * (completed / max(total, 1))),
            )
            if batch_index < len(batches) - 1:
                self._sleep_for_embedding_rate_limit(sum(chunk.token_count for chunk in batch))
        return embedded_chunks

    def _embedding_batches(self, chunks: list[BookChunk]) -> list[list[BookChunk]]:
        batches: list[list[BookChunk]] = []
        current: list[BookChunk] = []
        current_tokens = 0
        if self._llm.provider_name == "gemini":
            max_chunks = max(1, Config.GEMINI_EMBEDDING_MAX_BATCH_CHUNKS)
            max_tokens = max(1, Config.GEMINI_EMBEDDING_MAX_BATCH_INPUT_TOKENS)
        else:
            max_chunks = 100
            max_tokens = 10**12

        for chunk in chunks:
            would_exceed_chunks = len(current) >= max_chunks
            would_exceed_tokens = current and current_tokens + chunk.token_count > max_tokens
            if would_exceed_chunks or would_exceed_tokens:
                batches.append(current)
                current = []
                current_tokens = 0
            current.append(chunk)
            current_tokens += chunk.token_count

        if current:
            batches.append(current)
        return batches

    def _sleep_for_embedding_rate_limit(self, input_tokens: int) -> None:
        if self._llm.provider_name != "gemini":
            return
        requests_per_minute = max(1, Config.GEMINI_EMBEDDING_REQUESTS_PER_MINUTE)
        tokens_per_minute = max(1, Config.GEMINI_EMBEDDING_INPUT_TOKENS_PER_MINUTE)
        request_delay = 60 / requests_per_minute
        token_delay = 60 * (input_tokens / tokens_per_minute)
        jitter = random.uniform(0, max(0, Config.GEMINI_EMBEDDING_INTER_BATCH_JITTER_SECONDS))
        time.sleep(max(request_delay, token_delay) + jitter)

    def _update_embedding_progress(
        self,
        request_id: str | None,
        embedded_chunks: int,
        total_chunks: int,
        embedded_tokens: int,
        total_tokens: int,
    ) -> None:
        if request_id:
            self._books.update_ingestion_request_progress(
                request_id,
                embedded_chunks=embedded_chunks,
                total_chunks=total_chunks,
                embedded_tokens=embedded_tokens,
                total_tokens=total_tokens,
            )

    def _get_control_status(self, request_id: str | None) -> str:
        if not request_id:
            return "active"
        request = self._books.get_ingestion_request(request_id)
        return request.control_status if request else "active"

    def _is_control_status(self, request_id: str | None, status: str) -> bool:
        return self._get_control_status(request_id) == status

    def _update_ingestion(
        self,
        book_id: str,
        request_id: str | None,
        status: str,
        step: str | None = None,
        progress: int | None = None,
        error: str | None = None,
    ) -> None:
        ingestion = self._ingestion(
            status=status,
            step=step,
            progress=progress,
            error=error,
            request_id=request_id,
        )
        self._books.update_ingestion(book_id, ingestion)
        if request_id:
            self._books.update_ingestion_request(request_id, ingestion)

    @staticmethod
    def _ingestion(
        status: str,
        step: str | None = None,
        progress: int | None = None,
        error: str | None = None,
        request_id: str | None = None,
    ):
        from app.domain.books.models import IngestionInfo

        return IngestionInfo(status=status, progress=progress, step=step, error=error, request_id=request_id)


def _concise_error(exc: Exception) -> str:
    message = str(exc).splitlines()[0] if str(exc) else ""
    if message:
        return f"{type(exc).__name__}: {message}"[:2000]
    return type(exc).__name__
