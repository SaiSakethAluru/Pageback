from __future__ import annotations

from app.services.llm.base_provider import BaseLLMProvider


class ClaudeProvider(BaseLLMProvider):
    provider_name = "claude"
    recap_model = "claude-3-5-haiku-20241022"

    def recap(self, text_window: str, level: int) -> str:
        # TODO: implement using anthropic Python SDK, model claude-3-5-haiku-20241022
        raise NotImplementedError("Claude provider not yet implemented")

    def embed(self, text: str) -> list[float]:
        # TODO: implement using anthropic Python SDK, model claude-3-5-haiku-20241022
        raise NotImplementedError("Claude provider not yet implemented")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # TODO: implement using anthropic Python SDK, model claude-3-5-haiku-20241022
        raise NotImplementedError("Claude provider not yet implemented")
