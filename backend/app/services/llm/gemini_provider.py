from __future__ import annotations

from app.services.llm.base_provider import BaseLLMProvider


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def recap(self, text_window: str, level: int) -> str:
        # TODO: implement using google-generativeai Python SDK
        raise NotImplementedError("Gemini provider not yet implemented")

    def embed(self, text: str) -> list[float]:
        # TODO: implement using google-generativeai Python SDK
        raise NotImplementedError("Gemini provider not yet implemented")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # TODO: implement using google-generativeai Python SDK
        raise NotImplementedError("Gemini provider not yet implemented")
