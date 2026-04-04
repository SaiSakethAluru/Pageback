from __future__ import annotations

from app.domain.books.models import BookChunk
from app.domain.books.repositories import ChunkRepository
from app.domain.recap.models import LLMGateway, RecapCache, UsageLogRepository
from app.utils import token_counter
from config import Config

SEMANTIC_QUERY = "recent events characters and plot"


def _greedy_select(rows: list[BookChunk], token_budget: int) -> list[BookChunk]:
    selected: list[BookChunk] = []
    used_tokens = 0

    for row in rows:
        token_count = int(row.token_count or 0)
        if token_count <= 0:
            continue
        if used_tokens + token_count > token_budget:
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

    def resolve(self, book_id: str, position_char: int, level: int) -> str:
        token_budget = Config.RECAP_TOKEN_BUDGETS[level - 1]
        if level <= 2:
            selected = _greedy_select(
                self._chunks.find_before_position(book_id, int(position_char)),
                token_budget,
            )
        else:
            query_embedding = self._llm.embed(SEMANTIC_QUERY)
            selected = _greedy_select(
                self._chunks.search_similar(
                    book_id=book_id,
                    query_embedding=query_embedding,
                    max_char_offset=int(position_char),
                    token_budget=token_budget,
                ),
                token_budget,
            )

        return "\n\n".join(chunk.text for chunk in selected)


class RecapService:
    def __init__(
        self,
        window_resolver: WindowResolverService,
        cache: RecapCache,
        llm: LLMGateway,
        usage_logs: UsageLogRepository,
    ) -> None:
        self._window_resolver = window_resolver
        self._cache = cache
        self._llm = llm
        self._usage_logs = usage_logs

    def generate(self, user_id: str, book_id: str, position_char: int, level: int) -> dict:
        cache_key = self._cache.make_key(book_id, position_char, level)
        cached = self._cache.get(cache_key)
        if cached:
            return {"summary": cached, "level": level, "cached": True}

        text_window = self._window_resolver.resolve(book_id, position_char, level)
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

        return {"summary": summary, "level": level, "cached": False}


def _estimated_cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    if model == "gpt-4o-mini":
        return round((input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60), 6)
    return 0.0
