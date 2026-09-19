from app.application.recap.service import WindowResolverService
from app.domain.books.models import BookChunk


class ChunkRepositoryStub:
    def __init__(self, rows):
        self.rows = rows
        self.search_calls = []

    def find_before_position(self, _book_id, _position_char):
        return self.rows

    def find_by_chapter(self, _book_id, chapter_index):
        return [r for r in self.rows if r.chapter_index == chapter_index]

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


def test_level_one_respects_token_budget():
    rows = [
        BookChunk("book", 0, 0, 0, 100, 600, "first"),
        BookChunk("book", 0, 1, 0, 80, 600, "second"),
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


def test_resolve_char_from_cfi():
    rows = [
        BookChunk("book", 17, 0, 159114, 161364, 50, "chapter 17 text"),
    ]
    service = WindowResolverService(ChunkRepositoryStub(rows), LLMStub())

    char_offset = service.resolve_char_from_cfi("book", "epubcfi(/6/34!/4/2[chapter-6]/4[chapter-6-text]/222/1:0)")
    assert char_offset == 159114
