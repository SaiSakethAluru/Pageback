from __future__ import annotations

import random
import time

import requests

from app.services.llm.base_provider import BaseLLMProvider
from config import Config


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def recap(self, text_window: str, level: int) -> str:
        output_instruction = Config.RECAP_OUTPUT_INSTRUCTIONS[level - 1]
        system_prompt = (
            "You are a reading assistant. Recap only from the provided text. "
            "Do not use outside knowledge. Write in prose, in past tense, "
            "and stay factual and specific."
        )

        url = self._model_url(Config.GEMINI_RECAP_MODEL, "generateContent")
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

        response = requests.post(url, json=payload, headers=self._headers(), timeout=120)
        response.raise_for_status()
        data = response.json() or {}

        # Expected shape: candidates[0].content.parts[0].text
        try:
            return (data["candidates"][0]["content"]["parts"][0]["text"] or "").strip()
        except (KeyError, IndexError, TypeError):
            return (data.get("text") or "").strip()

    def embed(self, text: str) -> list[float]:
        url = self._model_url(Config.GEMINI_EMBEDDING_MODEL, "embedContent")
        payload = {"content": {"parts": [{"text": text}]}}

        response = requests.post(url, json=payload, headers=self._headers(), timeout=120)
        response.raise_for_status()
        data = response.json() or {}

        try:
            return self._embedding_values(data["embedding"])
        except (KeyError, TypeError):
            return []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        model = f"models/{Config.GEMINI_EMBEDDING_MODEL}"
        url = self._model_url(Config.GEMINI_EMBEDDING_MODEL, "batchEmbedContents")
        payload = {
            "requests": [
                {
                    "model": model,
                    "content": {"parts": [{"text": text}]},
                }
                for text in texts
            ],
        }

        response = self._post_with_rate_limit_retry(url, payload)
        response.raise_for_status()
        data = response.json() or {}

        embeddings = data.get("embeddings") or []
        if len(embeddings) != len(texts):
            return []
        try:
            return [self._embedding_values(embedding) for embedding in embeddings]
        except (KeyError, TypeError):
            return []

    @classmethod
    def _model_url(cls, model: str, method: str) -> str:
        return f"{cls.base_url}/{model}:{method}"

    @staticmethod
    def _headers() -> dict[str, str]:
        return {"x-goog-api-key": Config.GEMINI_API_KEY}

    @classmethod
    def _post_with_rate_limit_retry(cls, url: str, payload: dict) -> requests.Response:
        max_attempts = max(1, Config.GEMINI_EMBEDDING_RETRY_MAX_ATTEMPTS)
        delay = max(0, Config.GEMINI_EMBEDDING_RETRY_INITIAL_DELAY_SECONDS)
        for attempt in range(1, max_attempts + 1):
            response = requests.post(url, json=payload, headers=cls._headers(), timeout=120)
            if getattr(response, "status_code", None) != 429 or attempt == max_attempts:
                return response

            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    sleep_for = float(retry_after)
                except ValueError:
                    sleep_for = delay
            else:
                jitter = random.uniform(0, max(0, Config.GEMINI_EMBEDDING_RETRY_JITTER_SECONDS))
                sleep_for = delay + jitter

            time.sleep(sleep_for)
            delay = min(max(delay * 2, delay + 1), Config.GEMINI_EMBEDDING_RETRY_MAX_DELAY_SECONDS)
        return response

    @staticmethod
    def _embedding_values(embedding: dict) -> list[float]:
        values = embedding["values"]
        return [float(v) for v in values]

    @property
    def recap_model(self) -> str:
        return Config.GEMINI_RECAP_MODEL

    @property
    def embedding_model(self) -> str:
        return Config.GEMINI_EMBEDDING_MODEL
