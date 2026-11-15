from __future__ import annotations

import logging

from app.application.chat.dto import ChatMessageDTO, ChatResponseDTO
from app.application.recap.service import WindowResolverService
from app.domain.books.models import BookChunk
from app.domain.books.repositories import ChunkRepository
from app.domain.positions.repositories import ReadingPositionRepository
from app.domain.recap.models import LLMGateway, UsageLogRepository
from app.utils import token_counter

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = (
    "You are PageBack's reading companion and discussion partner, embedded beside the reader as they read.\n\n"
    "CRITICAL RULES:\n"
    "1. STRICTLY SPOILER-SAFE: You only know what has happened up to the reader's current point in the book. "
    "Ground your answers ONLY in the excerpts provided below of what the reader has read so far. "
    "NEVER reveal, hint at, or anticipate any plot developments, twists, deaths, or secrets from beyond their current position.\n"
    "2. If the user asks a question about something that hasn't happened yet or isn't explained up to this point in the book, "
    "state clearly that the book hasn't revealed this yet up to where they are currently reading.\n"
    "3. Be conversational, insightful, warm, and helpful. You can analyze character motives, themes, and details "
    "from the story so far."
)


class BookChatService:
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

    def chat(
        self,
        user_id: str,
        book_id: str,
        messages: list[ChatMessageDTO],
        position_char: int = 0,
        position_cfi: str | None = None,
    ) -> ChatResponseDTO:
        if not messages:
            return ChatResponseDTO(reply="Hello! How can I help you with what you've read so far?", grounded=False)

        latest_user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        if not latest_user_msg.strip():
            return ChatResponseDTO(reply="Please ask a question or share a thought about the book.", grounded=False)

        # Resolve reading position
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

        # Retrieve relevant chunks up to position_char
        # 1. Semantic search based on user's query
        semantic_chunks: list[BookChunk] = []
        try:
            query_embedding = self._llm.embed(latest_user_msg)
            semantic_chunks = self._chunks.search_similar(
                book_id=book_id,
                query_embedding=query_embedding,
                max_char_offset=int(position_char),
                token_budget=1800,
            )
        except Exception as e:
            logger.warning("Chat semantic search failed: %s", e)

        # 2. Recent chunks immediately prior to reading position
        recent_chunks: list[BookChunk] = []
        try:
            prior_chunks = self._chunks.find_before_position(book_id, int(position_char))
            recent_chunks = prior_chunks[:3]
        except Exception as e:
            logger.warning("Chat recent chunks fetch failed: %s", e)

        # Merge and deduplicate
        seen = set()
        selected: list[BookChunk] = []
        for c in recent_chunks + semantic_chunks:
            key = (c.chapter_index, c.chunk_index)
            if key not in seen:
                seen.add(key)
                selected.append(c)

        selected.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))
        context_text = "\n\n".join(c.text for c in selected) if selected else "No read text available."

        # Format conversation history
        history_lines = []
        for m in messages[-6:]:
            role_label = "Reader" if m.role == "user" else "Assistant"
            history_lines.append(f"{role_label}: {m.content}")

        conversation_str = "\n".join(history_lines)

        prompt = (
            f"--- STORY EXCERPTS (READ UP TO CURRENT POSITION) ---\n"
            f"{context_text}\n"
            f"--- END OF EXCERPTS ---\n\n"
            f"Conversation History:\n"
            f"{conversation_str}\n\n"
            f"Respond as the reading assistant (grounded strictly in the excerpts):"
        )

        reply = self._llm.generate(prompt, system_prompt=CHAT_SYSTEM_PROMPT)

        input_tokens = token_counter.count(prompt) + token_counter.count(CHAT_SYSTEM_PROMPT)
        output_tokens = token_counter.count(reply)
        self._usage_logs.log_summary_generation(
            user_id=user_id,
            provider_name=self._llm.provider_name,
            model_name=self._llm.recap_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
        )

        return ChatResponseDTO(reply=reply, grounded=bool(selected))
