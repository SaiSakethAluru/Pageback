from config import Config

from app.services.llm.gemini_provider import GeminiProvider


class FakeResponse:
    def __init__(self, data):
        self.data = data
        self.raised_for_status = False

    def raise_for_status(self):
        self.raised_for_status = True

    def json(self):
        return self.data


def test_embed_batch_uses_gemini_batch_endpoint(monkeypatch):
    calls = []
    response = FakeResponse(
        {
            "embeddings": [
                {"values": ["1", "2.5"]},
                {"values": [3, 4.25]},
            ]
        }
    )

    def fake_post(url, json, headers, timeout):
        calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return response

    monkeypatch.setattr(Config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-test")
    monkeypatch.setattr("app.services.llm.gemini_provider.requests.post", fake_post)

    embeddings = GeminiProvider().embed_batch(["first chunk", "second chunk"])

    assert embeddings == [[1.0, 2.5], [3.0, 4.25]]
    assert response.raised_for_status
    assert calls == [
        {
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-test:batchEmbedContents",
            "json": {
                "requests": [
                    {
                        "model": "models/gemini-embedding-test",
                        "content": {"parts": [{"text": "first chunk"}]},
                    },
                    {
                        "model": "models/gemini-embedding-test",
                        "content": {"parts": [{"text": "second chunk"}]},
                    },
                ]
            },
            "headers": {"x-goog-api-key": "test-key"},
            "timeout": 120,
        }
    ]
    assert "?key=" not in calls[0]["url"]


def test_embed_batch_skips_api_call_for_empty_input(monkeypatch):
    def fake_post(*args, **kwargs):
        raise AssertionError("Gemini API should not be called for an empty batch")

    monkeypatch.setattr("app.services.llm.gemini_provider.requests.post", fake_post)

    assert GeminiProvider().embed_batch([]) == []
