from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMProviderInfoDTO:
    provider: str
    recap_model: str
    embedding_model: str
