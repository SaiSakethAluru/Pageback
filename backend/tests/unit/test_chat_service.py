import pytest

from app.application.chat.dto import ChatMessageDTO
from app.application.chat.service import BookChatService
from app.domain.books.models import BookChunk
from app.domain.positions.models import ReadingPosition


class FakeChunkRepo:
    def __init__(self, chunks=None):
        self._chunks = chunks or []

    def search_similar(self, book_id, query_embedding, max_char_offset, token_budget):
        return [c for c in self._chunks if c.start_char <= max_char_offset]

    def find_before_position(self, book_id, position_char):
        return [c for c in self._chunks if c.start_char <= position_char]


class FakeLLM:
    provider_name = "test_llm"
    recap_model = "test_model"

    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return "Based on what you've read, Bunter is Lord Peter's loyal valet and former wartime comrade."


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


def test_chat_service_success():
    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=1,
            chunk_index=0,
            start_char=100,
            end_char=500,
            token_count=100,
            text="Bunter stepped forward with a polished magnifying glass.",
        )
    ]
    service = BookChatService(
        chunks=FakeChunkRepo(chunks),
        llm=FakeLLM(),
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        positions=FakePositions(),
    )

    messages = [
        ChatMessageDTO(role="user", content="Who is Bunter?")
    ]

    result = service.chat(
        user_id="u1",
        book_id="b1",
        messages=messages,
        position_char=600,
    )

    assert result.grounded is True
    assert "Bunter" in result.reply


def test_chat_service_empty_messages():
    service = BookChatService(
        chunks=FakeChunkRepo([]),
        llm=FakeLLM(),
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        positions=FakePositions(),
    )

    result = service.chat(
        user_id="u1",
        book_id="b1",
        messages=[],
    )

    assert result.grounded is False
    assert "help" in result.reply.lower()
