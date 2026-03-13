from __future__ import annotations

from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.openai_provider import OpenAIProvider
from config import Config


def get_provider(name: str | None = None) -> BaseLLMProvider:
    provider_name = name or Config.LLM_PROVIDER

    if provider_name == "openai":
        return OpenAIProvider()
    if provider_name == "claude":
        return ClaudeProvider()
    if provider_name == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown LLM provider: {provider_name}")
