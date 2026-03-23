from __future__ import annotations

import requests

from app.services.llm.base_provider import BaseLLMProvider
from config import Config


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def recap(self, text_window: str, level: int) -> str:
        output_instruction = Config.RECAP_OUTPUT_INSTRUCTIONS[level - 1]
        system_prompt = (
            "You are a reading assistant. Recap only from the provided text. "
            "Do not use outside knowledge. Write in prose, in past tense, "
            "and stay factual and specific."
        )

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{Config.GEMINI_RECAP_MODEL}:generateContent?key={Config.GEMINI_API_KEY}"
        )
        # Some Gemini API variants differ in whether `systemInstruction` is accepted.
        # To keep it robust, we include the "system" prompt directly in the user content.
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"{system_prompt}\n\n"
                                f"Write a recap in {output_instruction} based only on this text:\n\n"
                                f"{text_window}"
                            )
                        }
                    ],
                }
            ],
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json() or {}

        # Expected shape: candidates[0].content.parts[0].text
        try:
            return (data["candidates"][0]["content"]["parts"][0]["text"] or "").strip()
        except (KeyError, IndexError, TypeError):
            return (data.get("text") or "").strip()

    def embed(self, text: str) -> list[float]:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{Config.GEMINI_EMBEDDING_MODEL}:embedContent?key={Config.GEMINI_API_KEY}"
        )
        payload = {"content": {"parts": [{"text": text}]}}

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json() or {}

        try:
            values = data["embedding"]["values"]
            return [float(v) for v in values]
        except (KeyError, TypeError):
            return []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        # Keep it simple and reliable: call embed once per text.
        # Embedding batching can be optimized later once the API response
        # format is fully validated.
        return [self.embed(text) for text in texts]

    @property
    def recap_model(self) -> str:
        return Config.GEMINI_RECAP_MODEL

    @property
    def embedding_model(self) -> str:
        return Config.GEMINI_EMBEDDING_MODEL
