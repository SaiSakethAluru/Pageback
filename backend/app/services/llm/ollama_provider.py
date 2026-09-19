from __future__ import annotations

import re
import requests

from app.services.llm.base_provider import BaseLLMProvider
from config import Config


class OllamaProvider(BaseLLMProvider):
    """LLM gateway for a locally running Ollama server."""

    provider_name = "ollama"

    def recap(self, text_window: str, level: int) -> str:
        output_instruction = Config.RECAP_OUTPUT_INSTRUCTIONS[level - 1]
        system_prompt = (
            "You are a story recap assistant. Your task is to provide an engaging, immersive "
            "'Previously on...' recap to refresh the reader on the story so far, "
            "leading directly into where they are currently reading.\n\n"
            "STRICT RULES:\n"
            "1. IN-UNIVERSE NARRATIVE: Write in past-tense narrative prose. Recount the events directly as they happened "
            "in the story, focusing on characters, actions, revelations, and conflicts.\n"
            "2. NO META-LANGUAGE: NEVER refer to the book, writing, or author. DO NOT say 'the text describes', "
            "'the author writes', 'the excerpt shows', 'this chapter', 'the narrative recounts', 'the passage mentions', "
            "or refer to the author. Jump straight into the story events.\n"
            "3. IGNORE NON-STORY ELEMENTS: Completely ignore any table of contents, publisher notices, copyright info, "
            "exercise questions, dedications, preface notes, or allergen warnings. Focus purely on narrative plot events.\n"
            "4. ACCURACY: Stay strictly faithful to what occurred in the provided excerpts without making up outside facts."
        )
        response = self._post(
            "/api/chat",
            {
                "model": self.recap_model,
                "stream": False,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Write an immersive story recap ({output_instruction}) covering the events that took place:\n\n"
                            f"--- STORY EXCERPTS ---\n"
                            f"{text_window}\n"
                            f"--- END OF EXCERPTS ---"
                        ),
                    },
                ],
            },
        )
        content = str((response.json() or {}).get("message", {}).get("content") or "").strip()
        # Defensive cleanup in case a model outputs thinking/reasoning tags
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: dict = {
            "model": self.embedding_model,
            "input": texts,
        }
        if Config.OLLAMA_EMBEDDING_DIMENSIONS:
            payload["dimensions"] = Config.OLLAMA_EMBEDDING_DIMENSIONS

        response = self._post("/api/embed", payload)
        embeddings = (response.json() or {}).get("embeddings") or []
        if len(embeddings) != len(texts):
            raise RuntimeError(
                f"Ollama returned {len(embeddings)} embeddings for {len(texts)} chunks"
            )

        if Config.OLLAMA_EMBEDDING_DIMENSIONS and embeddings:
            actual_dim = len(embeddings[0])
            if actual_dim != Config.OLLAMA_EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Ollama model '{self.embedding_model}' returned {actual_dim}-dimensional embeddings, "
                    f"but {Config.OLLAMA_EMBEDDING_DIMENSIONS} is required by the database schema. "
                    f"Please ensure the configured model supports {Config.OLLAMA_EMBEDDING_DIMENSIONS} dimensions."
                )

        return [[float(value) for value in embedding] for embedding in embeddings]

    @staticmethod
    def _post(path: str, payload: dict) -> requests.Response:
        try:
            response = requests.post(f"{Config.OLLAMA_BASE_URL}{path}", json=payload, timeout=120)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {Config.OLLAMA_BASE_URL} ({exc}). "
                f"Start Ollama ('brew services start ollama' or 'ollama serve') and pull the configured models."
            ) from exc

    @property
    def recap_model(self) -> str:
        return Config.OLLAMA_RECAP_MODEL

    @property
    def embedding_model(self) -> str:
        return Config.OLLAMA_EMBEDDING_MODEL
