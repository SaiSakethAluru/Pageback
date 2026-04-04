from __future__ import annotations

from app.application.system.dto import LLMProviderInfoDTO
from app.domain.recap.models import LLMGateway


class SystemInfoService:
    def __init__(self, llm: LLMGateway) -> None:
        self._llm = llm

    def get_llm_provider_info(self) -> LLMProviderInfoDTO:
        return LLMProviderInfoDTO(
            provider=self._llm.provider_name,
            recap_model=self._llm.recap_model,
            embedding_model=self._llm.embedding_model,
        )
