from __future__ import annotations

from abc import ABC, abstractmethod


class RecapCache(ABC):
    @abstractmethod
    def get(self, cache_key: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, cache_key: str, summary: str, ttl_seconds: int = 86400) -> None:
        raise NotImplementedError

    @abstractmethod
    def make_key(self, book_id: str, position_char: int, level: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def invalidate_book(self, book_id: str) -> None:
        raise NotImplementedError


class LLMGateway(ABC):
    provider_name: str
    recap_model: str
    embedding_model: str

    @abstractmethod
    def recap(self, text_window: str, level: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


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
