from __future__ import annotations

from abc import abstractmethod

from app.domain.recap.models import LLMGateway


class BaseLLMProvider(LLMGateway):
    provider_name = "unknown"
    recap_model = ""
    embedding_model = ""

    @abstractmethod
    def recap(self, text_window: str, level: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
