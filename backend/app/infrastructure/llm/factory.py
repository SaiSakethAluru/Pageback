from __future__ import annotations

from app.domain.recap.models import LLMGateway
from app.services.llm.provider_factory import get_provider


def get_llm_gateway(name: str | None = None) -> LLMGateway:
    return get_provider(name)
