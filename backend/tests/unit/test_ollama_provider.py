import pytest
import requests
from config import Config

from app.services.llm.ollama_provider import OllamaProvider


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self.data


def test_ollama_provider_uses_configured_models_and_dimensions(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        if url.endswith("/api/chat"):
            return FakeResponse({"message": {"content": "A spoiler-safe recap."}})
        return FakeResponse({"embeddings": [[1.0, 2.5], [3.0, 4.25]]})

    monkeypatch.setattr(Config, "OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(Config, "OLLAMA_RECAP_MODEL", "recap-test")
    monkeypatch.setattr(Config, "OLLAMA_EMBEDDING_MODEL", "embedding-test")
    monkeypatch.setattr(Config, "OLLAMA_EMBEDDING_DIMENSIONS", 2)
    monkeypatch.setattr("app.services.llm.ollama_provider.requests.post", fake_post)

    provider = OllamaProvider()

    assert provider.recap("book text", 1) == "A spoiler-safe recap."
    assert provider.embed_batch(["first", "second"]) == [[1.0, 2.5], [3.0, 4.25]]
    assert calls[0]["url"] == "http://localhost:11434/api/chat"
    assert calls[0]["json"]["model"] == "recap-test"
    assert calls[1] == {
        "url": "http://localhost:11434/api/embed",
        "json": {"model": "embedding-test", "input": ["first", "second"], "dimensions": 2},
        "timeout": 120,
    }


def test_ollama_provider_strips_think_tags(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse(
            {
                "message": {
                    "content": "<think>\nLet me ponder this chapter...\n</think>\nThe protagonist escaped the dungeon."
                }
            }
        )

    monkeypatch.setattr("app.services.llm.ollama_provider.requests.post", fake_post)
    provider = OllamaProvider()
    assert provider.recap("some text", 1) == "The protagonist escaped the dungeon."


def test_ollama_provider_validates_dimension_mismatch(monkeypatch):
    def fake_post(url, json, timeout):
        return FakeResponse({"embeddings": [[0.1, 0.2]]})

    monkeypatch.setattr(Config, "OLLAMA_EMBEDDING_DIMENSIONS", 1536)
    monkeypatch.setattr("app.services.llm.ollama_provider.requests.post", fake_post)

    provider = OllamaProvider()
    with pytest.raises(RuntimeError, match="1536 is required by the database schema"):
        provider.embed_batch(["text"])


def test_ollama_provider_raises_on_unreachable_server(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("Connection refused")

    monkeypatch.setattr("app.services.llm.ollama_provider.requests.post", fake_post)
    provider = OllamaProvider()
    with pytest.raises(RuntimeError, match="Could not reach Ollama"):
        provider.recap("test", 1)
