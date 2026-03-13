from __future__ import annotations

from openai import OpenAI

from app.services.llm.base_provider import BaseLLMProvider
from config import Config


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"
    recap_model = "gpt-4o-mini"
    embedding_model = "text-embedding-3-small"

    def __init__(self) -> None:
        self.client = OpenAI()

    def recap(self, text_window: str, level: int) -> str:
        output_instruction = Config.RECAP_OUTPUT_INSTRUCTIONS[level - 1]
        response = self.client.chat.completions.create(
            model=self.recap_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a reading assistant. Recap only from the provided text. "
                        "Do not use outside knowledge. Write in prose, in past tense, "
                        "and stay factual and specific."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a recap in {output_instruction} based only on this text:\n\n{text_window}"
                    ),
                },
            ],
        )
        return response.choices[0].message.content or ""

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.embedding_model, input=texts)
        return [item.embedding for item in response.data]
