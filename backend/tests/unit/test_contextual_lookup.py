import pytest
from unittest.mock import MagicMock

from app.application.contextual_lookup.service import ContextualLookupService
from app.domain.books.models import BookChunk
from app.domain.positions.models import ReadingPosition


class FakeChunkRepo:
    def __init__(self, chunks=None):
        self._chunks = chunks or []

    def search_similar(self, book_id, query_embedding, max_char_offset, token_budget):
        return [c for c in self._chunks if c.start_char <= max_char_offset]

    def find_before_position(self, book_id, position_char):
        return [c for c in self._chunks if c.start_char <= position_char]

    def find_by_chapter(self, book_id, chapter_index):
        return [c for c in self._chunks if c.chapter_index == chapter_index]


class FakeLLM:
    provider_name = "test_llm"
    recap_model = "test_model"

    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Lord Peter Wimsey is an aristocratic amateur detective who appeared early in the book investigating the mysterious body in the bath."


class FakeWindowResolver:
    def resolve_char_from_cfi(self, book_id: str, position_cfi: str) -> int:
        return 1000


class FakeUsageLogs:
    def __init__(self):
        self.logged = []

    def log_summary_generation(self, user_id, provider_name, model_name, input_tokens, output_tokens, cost_usd):
        self.logged.append((user_id, provider_name, model_name, input_tokens, output_tokens))


class FakePositions:
    def __init__(self):
        self._positions = {}

    def get(self, user_id: str, book_id: str):
        return self._positions.get((user_id, book_id))

    def save(self, position: ReadingPosition):
        self._positions[(position.user_id, position.book_id)] = position


def test_contextual_lookup_with_matching_chunks():
    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=1,
            chunk_index=0,
            start_char=100,
            end_char=500,
            token_count=100,
            text="Lord Peter Wimsey lit a cigarette and smiled casually at Bunter.",
        )
    ]
    service = ContextualLookupService(
        chunks=FakeChunkRepo(chunks),
        llm=FakeLLM(),
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        positions=FakePositions(),
    )

    result = service.lookup(
        user_id="u1",
        book_id="b1",
        term="Lord Peter Wimsey",
        position_char=600,
    )

    assert result.term == "Lord Peter Wimsey"
    assert result.grounded is True
    assert "Lord Peter Wimsey" in result.explanation


def test_contextual_lookup_no_matching_chunks_prior_to_position():
    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=2,
            chunk_index=0,
            start_char=2000,
            end_char=2500,
            token_count=100,
            text="Lord Peter Wimsey arrived in Venice.",
        )
    ]
    service = ContextualLookupService(
        chunks=FakeChunkRepo(chunks),
        llm=FakeLLM(),
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        positions=FakePositions(),
    )

    result = service.lookup(
        user_id="u1",
        book_id="b1",
        term="Lord Peter Wimsey",
        position_char=500,  # reading position is before chunk starts
    )

    assert result.term == "Lord Peter Wimsey"
    assert result.grounded is False
    assert "No mentions" in result.explanation


def test_contextual_lookup_empty_term():
    service = ContextualLookupService(
        chunks=FakeChunkRepo([]),
        llm=FakeLLM(),
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        positions=FakePositions(),
    )

    result = service.lookup(
        user_id="u1",
        book_id="b1",
        term="   ",
        position_char=500,
    )

    assert result.grounded is False
    assert result.term == ""
