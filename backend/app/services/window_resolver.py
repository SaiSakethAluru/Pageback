from __future__ import annotations

from supabase import Client, create_client

from app.services.llm.provider_factory import get_provider
from config import Config

BOOK_CHUNKS_TABLE = "book_chunks"
SEMANTIC_QUERY = "recent events characters and plot"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


def _greedy_select(rows: list[dict], token_budget: int) -> list[dict]:
    selected: list[dict] = []
    used_tokens = 0

    for row in rows:
        token_count = int(row.get("token_count", 0) or 0)
        if token_count <= 0:
            continue
        if used_tokens + token_count > token_budget:
            continue
        selected.append(row)
        used_tokens += token_count
        if used_tokens >= token_budget:
            break

    return selected


def resolve(book_id: str, position_char: int, level: int) -> str:
    token_budget = Config.RECAP_TOKEN_BUDGETS[level - 1]
    position_char = int(position_char)
    supabase = _supabase()

    if level <= 2:
        response = (
            supabase.table(BOOK_CHUNKS_TABLE)
            .select("text, token_count, end_char")
            .eq("book_id", book_id)
            .lte("end_char", position_char)
            .order("end_char", desc=True)
            .execute()
        )
        selected = _greedy_select(response.data or [], token_budget)
    else:
        provider = get_provider()
        query_embedding = provider.embed(SEMANTIC_QUERY)
        response = (
            supabase.rpc(
                "match_chunks",
                {
                    "query_embedding": query_embedding,
                    "p_book_id": book_id,
                    "max_char_offset": position_char,
                    "token_budget": token_budget,
                },
            ).execute()
        )
        filtered = [
            row for row in (response.data or []) if int(row.get("end_char", 0) or 0) <= position_char
        ]
        selected = _greedy_select(filtered, token_budget)

    return "\n\n".join(str(row.get("text", "")) for row in selected)
