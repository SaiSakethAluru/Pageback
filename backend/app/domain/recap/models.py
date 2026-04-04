from __future__ import annotations

from abc import ABC, abstractmethod


class UsageLogRepository(ABC):
    @abstractmethod
    def log_summary_generation(
        self,
        user_id: str,
        provider_name: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        raise NotImplementedError
