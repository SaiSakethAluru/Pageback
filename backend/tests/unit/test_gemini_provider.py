from config import Config

from app.services.llm.gemini_provider import GeminiProvider


class FakeResponse:
    def __init__(self, data, status_code=200, headers=None):
        self.data = data
        self.status_code = status_code
        self.headers = headers or {}
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
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY", 1536)
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
                        "outputDimensionality": 1536,
                    },
                    {
                        "model": "models/gemini-embedding-test",
                        "content": {"parts": [{"text": "second chunk"}]},
                        "outputDimensionality": 1536,
                    },
                ]
            },
            "headers": {"x-goog-api-key": "test-key"},
            "timeout": 120,
        }
    ]
    assert "?key=" not in calls[0]["url"]


def test_embed_uses_configured_output_dimensionality(monkeypatch):
    calls = []
    response = FakeResponse({"embedding": {"values": ["1", "2.5"]}})

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
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY", 1536)
    monkeypatch.setattr("app.services.llm.gemini_provider.requests.post", fake_post)

    assert GeminiProvider().embed("semantic query") == [1.0, 2.5]
    assert response.raised_for_status
    assert calls == [
        {
            "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-test:embedContent",
            "json": {
                "content": {"parts": [{"text": "semantic query"}]},
                "outputDimensionality": 1536,
            },
            "headers": {"x-goog-api-key": "test-key"},
            "timeout": 120,
        }
    ]


def test_embed_batch_skips_api_call_for_empty_input(monkeypatch):
    def fake_post(*args, **kwargs):
        raise AssertionError("Gemini API should not be called for an empty batch")

    monkeypatch.setattr("app.services.llm.gemini_provider.requests.post", fake_post)

    assert GeminiProvider().embed_batch([]) == []


def test_embed_batch_retries_rate_limits(monkeypatch):
    calls = []
    responses = [
        FakeResponse({}, status_code=429, headers={"Retry-After": "0"}),
        FakeResponse({"embeddings": [{"values": [1, 2]}]}, status_code=200),
    ]

    def fake_post(url, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        return responses.pop(0)

    monkeypatch.setattr(Config, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_MODEL", "gemini-embedding-test")
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY", 1536)
    monkeypatch.setattr(Config, "GEMINI_EMBEDDING_RETRY_MAX_ATTEMPTS", 2)
    monkeypatch.setattr("app.services.llm.gemini_provider.requests.post", fake_post)

    assert GeminiProvider().embed_batch(["chunk"]) == [[1.0, 2.0]]
    assert len(calls) == 2
