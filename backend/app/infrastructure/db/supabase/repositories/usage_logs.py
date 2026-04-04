from __future__ import annotations

from collections.abc import Callable

from supabase import Client

from app.domain.recap.models import UsageLogRepository

LLM_USAGE_TABLE = "llm_usage"


class SupabaseUsageLogRepository(UsageLogRepository):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def log_summary_generation(
        self,
        user_id: str,
        provider_name: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        self._client_factory().table(LLM_USAGE_TABLE).insert(
            {
                "user_id": user_id,
                "provider": provider_name,
                "model": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": cost_usd,
            }
        ).execute()
