from app.application.recap.service import WindowResolverService
from app.domain.books.models import BookChunk


class ChunkRepositoryStub:
    def __init__(self, rows):
        self.rows = rows
        self.search_calls = []

    def find_before_position(self, _book_id, _position_char):
        return self.rows

    def search_similar(self, **kwargs):
        self.search_calls.append(kwargs)
        return self.rows


class LLMStub:
    provider_name = "stub"
    recap_model = "stub-model"
    embedding_model = "stub-embedding"

    def embed(self, _text):
        return [0.1, 0.2]

    def recap(self, text_window, level):
        return f"{level}:{text_window}"

    def embed_batch(self, texts):
        return [[0.1, 0.2] for _ in texts]


def test_level_one_uses_150_token_budget():
    rows = [
        BookChunk("book", 0, 0, 0, 100, 100, "first"),
        BookChunk("book", 0, 1, 0, 80, 100, "second"),
    ]
    service = WindowResolverService(ChunkRepositoryStub(rows), LLMStub())

    result = service.resolve("book", 100, 1)

    assert result == "first"


def test_spoiler_fence_is_respected():
    rows = [BookChunk("book", 0, 0, 0, 90, 50, "allowed")]
    service = WindowResolverService(ChunkRepositoryStub(rows), LLMStub())

    result = service.resolve("book", 100, 1)

    assert "allowed" in result


def test_levels_three_to_five_use_match_chunks():
    rows = [
        BookChunk("book", 0, 0, 0, 90, 100, "chunk one"),
        BookChunk("book", 0, 1, 0, 95, 100, "chunk two"),
    ]
    repo = ChunkRepositoryStub(rows)
    service = WindowResolverService(repo, LLMStub())

    result = service.resolve("book", 100, 3)

    assert repo.search_calls[0]["book_id"] == "book"
    assert result == "chunk one\n\nchunk two"


def test_chunks_join_with_double_newlines():
    rows = [
        BookChunk("book", 0, 0, 0, 70, 50, "alpha"),
        BookChunk("book", 0, 1, 0, 50, 50, "beta"),
    ]
    service = WindowResolverService(ChunkRepositoryStub(rows), LLMStub())

    result = service.resolve("book", 100, 1)

    assert result == "alpha\n\nbeta"
