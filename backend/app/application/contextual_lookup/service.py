from __future__ import annotations

import logging

from app.application.contextual_lookup.dto import ContextualLookupResultDTO
from app.application.recap.service import WindowResolverService
from app.domain.books.models import BookChunk
from app.domain.books.repositories import ChunkRepository
from app.domain.positions.repositories import ReadingPositionRepository
from app.domain.recap.models import LLMGateway, UsageLogRepository
from app.utils import token_counter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are PageBack's spoiler-safe reading companion. "
    "The reader has asked to look up a book-specific term, character, or place.\n\n"
    "CRITICAL RULES:\n"
    "1. ZERO SPOILERS: Your answer MUST be strictly grounded in the excerpts provided below of what the reader has read so far. "
    "Do NOT mention or hint at any events, deaths, betrayals, twists, or developments that occur later in the story or outside knowledge.\n"
    "2. If the provided excerpts do not mention or provide enough detail to identify this term, state clearly that "
    "this term has not yet been introduced or detailed in the story up to this reading position.\n"
    "3. Keep your explanation concise, engaging, and in past-tense narrative prose (1-2 paragraphs)."
)


class ContextualLookupService:
    def __init__(
        self,
        chunks: ChunkRepository,
        llm: LLMGateway,
        window_resolver: WindowResolverService,
        usage_logs: UsageLogRepository,
        positions: ReadingPositionRepository | None = None,
    ) -> None:
        self._chunks = chunks
        self._llm = llm
        self._window_resolver = window_resolver
        self._usage_logs = usage_logs
        self._positions = positions

    def lookup(
        self,
        user_id: str,
        book_id: str,
        term: str,
        position_char: int = 0,
        position_cfi: str | None = None,
    ) -> ContextualLookupResultDTO:
        clean_term = term.strip()
        if not clean_term:
            return ContextualLookupResultDTO(term="", explanation="No term provided.", grounded=False)

        # Resolve position if needed
        if position_char <= 0:
            if not position_cfi and self._positions:
                saved = self._positions.get(user_id, book_id)
                if saved:
                    if saved.position_char and saved.position_char > 0:
                        position_char = saved.position_char
                    if saved.position_cfi:
                        position_cfi = saved.position_cfi

        if position_char <= 0 and position_cfi:
            resolved = self._window_resolver.resolve_char_from_cfi(book_id, position_cfi)
            if resolved > 0:
                position_char = resolved

        # Step 1: Semantic search for the term
        semantic_query = f"{clean_term} character place term description events"
        try:
            query_embedding = self._llm.embed(semantic_query)
            similar_chunks = self._chunks.search_similar(
                book_id=book_id,
                query_embedding=query_embedding,
                max_char_offset=int(position_char),
                token_budget=2000,
            )
        except Exception as e:
            logger.warning("Semantic search failed for term '%s': %s", clean_term, e)
            similar_chunks = []

        # Step 2: Also look for exact keyword mentions in prior chunks
        keyword_chunks: list[BookChunk] = []
        try:
            all_prior = self._chunks.find_before_position(book_id, int(position_char))
            term_lower = clean_term.lower()
            for chunk in all_prior:
                if term_lower in chunk.text.lower():
                    keyword_chunks.append(chunk)
                    if len(keyword_chunks) >= 3:
                        break
        except Exception as e:
            logger.warning("Keyword chunk search failed: %s", e)

        # Merge and deduplicate
        seen = set()
        selected: list[BookChunk] = []
        for c in keyword_chunks + similar_chunks:
            key = (c.chapter_index, c.chunk_index)
            if key not in seen:
                seen.add(key)
                selected.append(c)

        selected.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))

        # Check if we have any relevant chunks
        if not selected:
            return ContextualLookupResultDTO(
                term=clean_term,
                explanation=f"No mentions of '{clean_term}' were found in the book prior to your current reading position. It may not have been introduced yet.",
                grounded=False,
            )

        context_text = "\n\n".join(chunk.text for chunk in selected)

        prompt = (
            f"Explain who or what '{clean_term}' is in the story, based solely on what the reader has encountered so far:\n\n"
            f"--- STORY EXCERPTS (READ SO FAR) ---\n"
            f"{context_text}\n"
            f"--- END OF EXCERPTS ---"
        )

        explanation = self._llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        input_tokens = token_counter.count(prompt) + token_counter.count(SYSTEM_PROMPT)
        output_tokens = token_counter.count(explanation)
        self._usage_logs.log_summary_generation(
            user_id=user_id,
            provider_name=self._llm.provider_name,
            model_name=self._llm.recap_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
        )

        return ContextualLookupResultDTO(
            term=clean_term,
            explanation=explanation,
            grounded=True,
        )
