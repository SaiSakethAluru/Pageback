import logging
import re

from app.application.errors import RecapUnavailableError
from app.application.recap.dto import RecapResultDTO
from app.domain.books.models import BookChunk
from app.domain.books.repositories import ChunkRepository
from app.domain.positions.models import ReadingPosition
from app.domain.positions.repositories import ReadingPositionRepository
from app.domain.recap.models import LLMGateway, RecapCache, UsageLogRepository
from app.utils import token_counter
from config import Config

SEMANTIC_QUERY = "recent events characters and plot"
logger = logging.getLogger(__name__)


def _greedy_select(rows: list[BookChunk], token_budget: int) -> list[BookChunk]:
    selected: list[BookChunk] = []
    used_tokens = 0

    for row in rows:
        token_count = int(row.token_count or 0)
        if token_count <= 0:
            continue
        if selected and used_tokens + token_count > token_budget:
            continue
        selected.append(row)
        used_tokens += token_count
        if used_tokens >= token_budget:
            break

    return selected


class WindowResolverService:
    def __init__(self, chunks: ChunkRepository, llm: LLMGateway) -> None:
        self._chunks = chunks
        self._llm = llm

    def resolve_char_from_cfi(self, book_id: str, position_cfi: str) -> int:
        match = re.search(r"/6/(\d+)!", position_cfi)
        if not match:
            return 0
        spine_index = int(match.group(1)) // 2
        chapter_chunks = self._chunks.find_by_chapter(book_id, spine_index)
        if chapter_chunks:
            return chapter_chunks[0].start_char
        return 0

    def resolve(
        self,
        book_id: str,
        position_char: int,
        level: int,
        position_cfi: str | None = None,
    ) -> str:
        if position_char <= 0 and position_cfi:
            resolved_char = self.resolve_char_from_cfi(book_id, position_cfi)
            if resolved_char > 0:
                position_char = resolved_char

        token_budget = Config.RECAP_TOKEN_BUDGETS[level - 1]
        if level <= 2:
            selected = _greedy_select(
                self._chunks.find_before_position(book_id, int(position_char)),
                token_budget,
            )
        else:
            recent_chunks = self._chunks.find_before_position(book_id, int(position_char))
            recent_budget = min(1500, token_budget // 3)
            recent_selected = _greedy_select(recent_chunks, recent_budget)

            remaining_budget = max(500, token_budget - sum(c.token_count for c in recent_selected))
            query_embedding = self._llm.embed(SEMANTIC_QUERY)
            semantic_selected = _greedy_select(
                self._chunks.search_similar(
                    book_id=book_id,
                    query_embedding=query_embedding,
                    max_char_offset=int(position_char),
                    token_budget=remaining_budget,
                ),
                remaining_budget,
            )
            seen_keys = set()
            selected = []
            for chunk in recent_selected + semantic_selected:
                key = (chunk.chapter_index, chunk.chunk_index)
                if key not in seen_keys:
                    seen_keys.add(key)
                    selected.append(chunk)

        selected.sort(key=lambda c: (c.chapter_index, c.chunk_index, c.start_char))
        return "\n\n".join(chunk.text for chunk in selected)



class RecapService:
    def __init__(
        self,
        window_resolver: WindowResolverService,
        cache: RecapCache,
        llm: LLMGateway,
        usage_logs: UsageLogRepository,
        positions: ReadingPositionRepository | None = None,
    ) -> None:
        self._window_resolver = window_resolver
        self._cache = cache
        self._llm = llm
        self._usage_logs = usage_logs
        self._positions = positions

    def generate(
        self,
        user_id: str,
        book_id: str,
        position_char: int,
        level: int,
        position_cfi: str | None = None,
    ) -> RecapResultDTO:
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
                if self._positions:
                    try:
                        self._positions.save(
                            ReadingPosition(
                                user_id=user_id,
                                book_id=book_id,
                                position_cfi=position_cfi,
                                position_char=position_char,
                            )
                        )
                    except Exception:
                        pass

        cache_key = self._cache.make_key(book_id, position_char, level)
        cached = self._cache.get(cache_key)
        if cached:
            return RecapResultDTO(summary=cached, level=level, cached=True)

        text_window = self._window_resolver.resolve(book_id, position_char, level, position_cfi=position_cfi)
        if not text_window.strip():
            logger.info(
                "Recap unavailable because no spoiler-safe context was found for book_id=%s position_char=%s level=%s position_cfi=%s",
                book_id,
                position_char,
                level,
                position_cfi,
            )
            raise RecapUnavailableError(
                "There is not enough spoiler-safe context here to generate a recap yet. "
                "Try again after reading a bit further."
            )
        summary = self._llm.recap(text_window, level)
        self._cache.set(cache_key, summary)

        input_tokens = token_counter.count(text_window)
        output_tokens = token_counter.count(summary)
        self._usage_logs.log_summary_generation(
            user_id=user_id,
            provider_name=self._llm.provider_name,
            model_name=self._llm.recap_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=_estimated_cost_usd(input_tokens, output_tokens, self._llm.recap_model),
        )

        return RecapResultDTO(summary=summary, level=level, cached=False)


def _estimated_cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    if model == "gpt-4o-mini":
        return round((input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60), 6)
    return 0.0
