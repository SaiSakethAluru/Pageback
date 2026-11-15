import pytest

from app.application.books.series_context import SeriesContextService
from app.application.books.service import BookService
from app.application.chat.dto import ChatMessageDTO
from app.application.chat.service import BookChatService
from app.application.contextual_lookup.service import ContextualLookupService
from app.application.recap.service import RecapService
from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo
from app.domain.books.repositories import BookRepository, BookStorage, ChunkRepository


class MemoryBookRepo(BookRepository):
    def __init__(self, books=None):
        self._books = {b.id: b for b in (books or [])}

    def create(self, book: Book) -> None:
        self._books[book.id] = book

    def get_by_id(self, book_id: str, user_id: str) -> Book | None:
        b = self._books.get(book_id)
        if b and b.user_id == user_id:
            return b
        return None

    def list_by_user(self, user_id: str) -> list[Book]:
        return [b for b in self._books.values() if b.user_id == user_id]

    def update_metadata(self, book_id: str, user_id: str, metadata: BookMetadata) -> Book | None:
        b = self.get_by_id(book_id, user_id)
        if not b:
            return None
        updated = Book(
            id=b.id,
            user_id=b.user_id,
            storage_path=b.storage_path,
            metadata=metadata,
            ingestion=b.ingestion,
            cover_path=b.cover_path,
            created_at=b.created_at,
        )
        self._books[book_id] = updated
        return updated

    def update_cover_path(self, book_id: str, cover_path: str) -> None:
        pass

    def update_ingestion(self, book_id: str, ingestion: IngestionInfo) -> None:
        pass

    def create_ingestion_request(self, request) -> None:
        pass

    def update_ingestion_request(self, request_id: str, ingestion: IngestionInfo) -> None:
        pass

    def mark_ingestion_request_started(self, request_id: str) -> None:
        pass

    def mark_ingestion_request_finished(self, request_id: str, status: str, error_type=None, error_message=None) -> None:
        pass

    def update_ingestion_request_task_id(self, request_id: str, task_id: str | None) -> None:
        pass

    def get_latest_ingestion_request(self, book_id: str, user_id: str):
        return None

    def get_ingestion_request(self, request_id: str):
        return None

    def list_ingestion_requests_by_user(self, user_id: str, statuses=None):
        return []

    def update_ingestion_request_progress(self, request_id: str, embedded_chunks: int, total_chunks: int, embedded_tokens: int, total_tokens: int) -> None:
        pass

    def update_ingestion_request_control(self, request_id: str, control_status: str, status=None) -> None:
        pass

    def ensure_model_config(self, provider: str, recap_model: str, embedding_model: str) -> str:
        return "model-cfg-1"

    def delete(self, book_id: str, user_id: str) -> None:
        self._books.pop(book_id, None)


class MemoryChunkRepo(ChunkRepository):
    def __init__(self, chunks=None):
        self._chunks = list(chunks or [])

    def delete_by_book(self, book_id: str) -> None:
        self._chunks = [c for c in self._chunks if c.book_id != book_id]

    def replace_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        self.delete_by_book(book_id)
        self._chunks.extend(chunks)

    def upsert_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        self._chunks.extend(chunks)

    def find_embedded_keys(self, book_id: str) -> set[tuple[int, int]]:
        return set()

    def find_before_position(self, book_id: str, position_char: int) -> list[BookChunk]:
        return [c for c in self._chunks if c.book_id == book_id and c.start_char <= position_char]

    def find_by_chapter(self, book_id: str, chapter_index: int) -> list[BookChunk]:
        return [c for c in self._chunks if c.book_id == book_id and c.chapter_index == chapter_index]

    def search_similar(self, book_id: str, query_embedding: list[float], max_char_offset: int, token_budget: int) -> list[BookChunk]:
        return [c for c in self._chunks if c.book_id == book_id and c.start_char <= max_char_offset]


class FakeLLM:
    provider_name = "fake_provider"
    recap_model = "fake_model"

    def __init__(self):
        self.prompts = []

    def embed(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        self.prompts.append(prompt)
        return "Fake AI response grounded in series."

    def recap(self, text: str, level: int) -> str:
        self.prompts.append(text)
        return "Fake series recap summary."


class FakeStorage(BookStorage):
    def upload(self, path: str, content: bytes, content_type: str) -> None:
        pass

    def download(self, path: str) -> bytes:
        return b""

    def remove_many(self, paths: list[str]) -> None:
        pass

    def create_signed_url(self, path: str, expires_in_seconds: int) -> str | None:
        return f"https://signed/{path}"


class FakeUsageLogs:
    def log_summary_generation(self, user_id, provider_name, model_name, input_tokens, output_tokens, cost_usd):
        pass


class FakeWindowResolver:
    def resolve(self, book_id, position_char, level, position_cfi=None):
        return "Current book text window excerpt."

    def resolve_char_from_cfi(self, book_id, position_cfi):
        return 0


class FakeCache:
    def __init__(self):
        self.cache = {}

    def make_key(self, book_id, position_char, level):
        return f"{book_id}:{position_char}:{level}"

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value


def make_book(book_id: str, title: str, series_name: str | None, series_order: float | None) -> Book:
    return Book(
        id=book_id,
        user_id="user-123",
        storage_path=f"storage/{book_id}.epub",
        metadata=BookMetadata(
            title=title,
            author="Brandon Sanderson",
            series_name=series_name,
            series_order=series_order,
        ),
        ingestion=IngestionInfo(status="complete"),
    )


def test_get_preceding_books_filters_and_orders_properly():
    b1 = make_book("b1", "The Final Empire", "Mistborn", 1.0)
    b2 = make_book("b2", "The Well of Ascension", "Mistborn", 2.0)
    b3 = make_book("b3", "The Hero of Ages", "Mistborn", 3.0)
    other = make_book("b_other", "Elantris", "Elantris", 1.0)

    books_repo = MemoryBookRepo([b1, b2, b3, other])
    chunks_repo = MemoryChunkRepo()
    llm = FakeLLM()

    service = SeriesContextService(books_repo, chunks_repo, llm)

    # For Book 2, preceding book is Book 1
    preceding_b2 = service.get_preceding_books("user-123", "b2")
    assert len(preceding_b2) == 1
    assert preceding_b2[0].id == "b1"

    # For Book 3, preceding books are Book 1 and Book 2 in order
    preceding_b3 = service.get_preceding_books("user-123", "b3")
    assert len(preceding_b3) == 2
    assert [b.id for b in preceding_b3] == ["b1", "b2"]

    # For Book 1, preceding books is empty
    preceding_b1 = service.get_preceding_books("user-123", "b1")
    assert len(preceding_b1) == 0


def test_series_context_for_term_retrieves_preceding_book_chunks():
    b1 = make_book("b1", "The Final Empire", "Mistborn", 1.0)
    b2 = make_book("b2", "The Well of Ascension", "Mistborn", 2.0)

    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=1,
            chunk_index=0,
            start_char=0,
            end_char=500,
            token_count=100,
            text="Kelsier was the Survivor of Hathsin, an allomancer who led the rebellion against the Lord Ruler.",
        ),
        BookChunk(
            book_id="b2",
            chapter_index=1,
            chunk_index=0,
            start_char=0,
            end_char=500,
            token_count=100,
            text="Vin stood on the walls of Luthadel, feeling the mists swirl around her.",
        ),
    ]

    books_repo = MemoryBookRepo([b1, b2])
    chunks_repo = MemoryChunkRepo(chunks)
    llm = FakeLLM()

    service = SeriesContextService(books_repo, chunks_repo, llm)

    context = service.resolve_context_for_term("user-123", "b2", "Kelsier")
    assert "--- PREVIOUS BOOKS IN THE SERIES: Mistborn ---" in context
    assert "Kelsier was the Survivor of Hathsin" in context
    assert "The Final Empire" in context


def test_contextual_lookup_uses_series_context_when_not_in_current_book():
    b1 = make_book("b1", "The Final Empire", "Mistborn", 1.0)
    b2 = make_book("b2", "The Well of Ascension", "Mistborn", 2.0)

    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=1,
            chunk_index=0,
            start_char=0,
            end_char=500,
            token_count=100,
            text="The Lord Ruler was an immortal tyrant who conquered Scadrial a thousand years ago.",
        ),
    ]

    books_repo = MemoryBookRepo([b1, b2])
    chunks_repo = MemoryChunkRepo(chunks)
    llm = FakeLLM()
    series_context = SeriesContextService(books_repo, chunks_repo, llm)

    lookup_service = ContextualLookupService(
        chunks=chunks_repo,
        llm=llm,
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        series_context=series_context,
    )

    # In Book 2 at position 100, "Lord Ruler" isn't mentioned in Book 2 yet, but is in Book 1
    result = lookup_service.lookup("user-123", "b2", "Lord Ruler", position_char=100)
    assert result.grounded is True
    assert "The Lord Ruler was an immortal tyrant" in llm.prompts[-1]


def test_chat_service_injects_preceding_series_backstory():
    b1 = make_book("b1", "The Final Empire", "Mistborn", 1.0)
    b2 = make_book("b2", "The Well of Ascension", "Mistborn", 2.0)

    chunks = [
        BookChunk(
            book_id="b1",
            chapter_index=1,
            chunk_index=0,
            start_char=0,
            end_char=500,
            token_count=100,
            text="The Eleventh Metal was a mythical allomantic metal Kelsier sought to defeat the Lord Ruler.",
        ),
    ]

    books_repo = MemoryBookRepo([b1, b2])
    chunks_repo = MemoryChunkRepo(chunks)
    llm = FakeLLM()
    series_context = SeriesContextService(books_repo, chunks_repo, llm)

    chat_service = BookChatService(
        chunks=chunks_repo,
        llm=llm,
        window_resolver=FakeWindowResolver(),
        usage_logs=FakeUsageLogs(),
        series_context=series_context,
    )

    response = chat_service.chat(
        user_id="user-123",
        book_id="b2",
        messages=[ChatMessageDTO(role="user", content="What was the eleventh metal again?")],
        position_char=50,
    )

    assert response.grounded is True
    assert "PREVIOUS BOOKS IN THE SERIES: Mistborn" in llm.prompts[-1]
    assert "The Eleventh Metal was a mythical allomantic metal" in llm.prompts[-1]


def test_book_service_series_metadata_update_and_lookup():
    b1 = make_book("b1", "Book One", None, None)
    repo = MemoryBookRepo([b1])
    service = BookService(repo, FakeStorage(), MemoryChunkRepo())

    updated = service.update_metadata(
        book_id="b1",
        user_id="user-123",
        title="Book One",
        author="Brandon Sanderson",
        series_name="Stormlight Archive",
        series_order=1.0,
    )

    assert updated is not None
    assert updated.series_name == "Stormlight Archive"
    assert updated.series_order == 1.0

    b2 = make_book("b2", "Book Two", "Stormlight Archive", 2.0)
    repo.create(b2)

    prev_books = service.get_previous_books_in_series("b2", "user-123")
    assert len(prev_books) == 1
    assert prev_books[0].id == "b1"
