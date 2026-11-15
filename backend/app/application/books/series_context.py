from __future__ import annotations

import logging

from app.domain.books.models import Book, BookChunk
from app.domain.books.repositories import BookRepository, ChunkRepository
from app.domain.recap.models import LLMGateway

logger = logging.getLogger(__name__)


class SeriesContextService:
    def __init__(
        self,
        books: BookRepository,
        chunks: ChunkRepository,
        llm: LLMGateway,
    ) -> None:
        self._books = books
        self._chunks = chunks
        self._llm = llm

    def get_preceding_books(self, user_id: str, book_id: str) -> list[Book]:
        current_book = self._books.get_by_id(book_id, user_id)
        if not current_book or not current_book.metadata.series_name:
            return []
        current_order = current_book.metadata.series_order
        if current_order is None:
            return []
        series_books = self._books.list_books_in_series(user_id, current_book.metadata.series_name)
        return [
            b
            for b in series_books
            if b.id != book_id
            and b.metadata.series_order is not None
            and b.metadata.series_order < current_order
        ]

    def resolve_context_for_term(
        self,
        user_id: str,
        book_id: str,
        term: str,
        max_tokens: int = 1200,
    ) -> str:
        """Finds relevant mentions or backstory about a term from earlier books in the series."""
        preceding = self.get_preceding_books(user_id, book_id)
        if not preceding:
            return ""

        current_book = self._books.get_by_id(book_id, user_id)
        series_name = current_book.metadata.series_name if current_book else "Series"

        context_parts: list[str] = []
        tokens_per_book = max(400, max_tokens // len(preceding))

        query_embedding = None
        try:
            query_embedding = self._llm.embed(f"{term} character place term backstory events")
        except Exception as e:
            logger.warning("Series embedding lookup failed for term '%s': %s", term, e)

        for prev_book in preceding:
            book_title = prev_book.metadata.title or f"Book {prev_book.metadata.series_order}"
            term_lower = term.lower()

            # 1. Exact keyword search in preceding book chunks
            exact_chunks: list[BookChunk] = []
            try:
                all_chunks = self._chunks.find_before_position(prev_book.id, 999999999)
                for c in all_chunks:
                    if term_lower in c.text.lower():
                        exact_chunks.append(c)
                        if len(exact_chunks) >= 3:
                            break
            except Exception as e:
                logger.warning("Keyword chunk search failed in preceding book %s: %s", prev_book.id, e)

            # 2. Semantic search in preceding book chunks
            sem_chunks: list[BookChunk] = []
            if query_embedding:
                try:
                    sem_chunks = self._chunks.search_similar(
                        book_id=prev_book.id,
                        query_embedding=query_embedding,
                        max_char_offset=999999999,
                        token_budget=tokens_per_book,
                    )
                except Exception as e:
                    logger.warning("Semantic chunk search failed in preceding book %s: %s", prev_book.id, e)

            # Merge and deduplicate
            seen = set()
            selected: list[BookChunk] = []
            for c in exact_chunks + sem_chunks:
                key = (c.chapter_index, c.chunk_index)
                if key not in seen:
                    seen.add(key)
                    selected.append(c)
                    if len(selected) >= 3:
                        break

            if selected:
                selected.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))
                book_text = "\n\n".join(c.text for c in selected)
                order_tag = (
                    f"Book #{prev_book.metadata.series_order}"
                    if prev_book.metadata.series_order is not None
                    else ""
                )
                context_parts.append(f"[{book_title} ({order_tag})]:\n{book_text}")

        if not context_parts:
            return ""

        return (
            f"--- PREVIOUS BOOKS IN THE SERIES: {series_name} ---\n"
            + "\n\n".join(context_parts)
            + "\n--- END OF PREVIOUS BOOKS ---\n"
        )

    def resolve_context_for_chat(
        self,
        user_id: str,
        book_id: str,
        query: str,
        max_tokens: int = 1000,
    ) -> str:
        """Finds relevant lore or backstory from earlier books in the series for chat questions."""
        preceding = self.get_preceding_books(user_id, book_id)
        if not preceding:
            return ""

        current_book = self._books.get_by_id(book_id, user_id)
        series_name = current_book.metadata.series_name if current_book else "Series"

        query_embedding = None
        try:
            query_embedding = self._llm.embed(query)
        except Exception as e:
            logger.warning("Series embedding lookup failed for chat query: %s", e)

        context_parts: list[str] = []
        tokens_per_book = max(400, max_tokens // len(preceding))

        for prev_book in preceding:
            book_title = prev_book.metadata.title or f"Book {prev_book.metadata.series_order}"
            sem_chunks: list[BookChunk] = []
            if query_embedding:
                try:
                    sem_chunks = self._chunks.search_similar(
                        book_id=prev_book.id,
                        query_embedding=query_embedding,
                        max_char_offset=999999999,
                        token_budget=tokens_per_book,
                    )
                except Exception as e:
                    logger.warning("Semantic chunk search failed in preceding book %s: %s", prev_book.id, e)

            if sem_chunks:
                sem_chunks.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))
                book_text = "\n\n".join(c.text for c in sem_chunks[:3])
                order_tag = (
                    f"Book #{prev_book.metadata.series_order}"
                    if prev_book.metadata.series_order is not None
                    else ""
                )
                context_parts.append(f"[{book_title} ({order_tag})]:\n{book_text}")

        if not context_parts:
            return ""

        return (
            f"--- PREVIOUS BOOKS IN THE SERIES: {series_name} ---\n"
            + "\n\n".join(context_parts)
            + "\n--- END OF PREVIOUS BOOKS ---\n"
        )

    def resolve_context_for_recap(
        self,
        user_id: str,
        book_id: str,
        max_tokens: int = 800,
    ) -> str:
        """Finds summary or resolution context from earlier books in the series for recaps."""
        preceding = self.get_preceding_books(user_id, book_id)
        if not preceding:
            return ""

        current_book = self._books.get_by_id(book_id, user_id)
        series_name = current_book.metadata.series_name if current_book else "Series"

        context_parts: list[str] = []
        tokens_per_book = max(300, max_tokens // len(preceding))

        for prev_book in preceding:
            book_title = prev_book.metadata.title or f"Book {prev_book.metadata.series_order}"
            try:
                all_chunks = self._chunks.find_before_position(prev_book.id, 999999999)
                recap_chunks = all_chunks[:2] if all_chunks else []
                if recap_chunks:
                    recap_chunks.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))
                    book_text = "\n\n".join(c.text for c in recap_chunks)
                    order_tag = (
                        f"Book #{prev_book.metadata.series_order}"
                        if prev_book.metadata.series_order is not None
                        else ""
                    )
                    context_parts.append(f"[{book_title} ({order_tag})]:\n{book_text}")
            except Exception as e:
                logger.warning("Failed retrieving recap chunks for preceding book %s: %s", prev_book.id, e)

        if not context_parts:
            return ""

        return (
            f"--- PRECEDING BACKSTORY IN SERIES: {series_name} ---\n"
            + "\n\n".join(context_parts)
            + "\n--- END OF PRECEDING BACKSTORY ---\n"
        )
