from app.application.auth.service import AuthApplicationService
from app.application.books.service import BookService
from app.application.recap.service import RecapService, WindowResolverService
from app.domain.auth.models import AuthIdentity, User
from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo
from app.domain.positions.models import ReadingPosition


class UserRepoStub:
    def __init__(self):
        self.user = User("u1", "u@example.com", "User", None, "google")

    def get_by_id(self, user_id: str):
        return self.user if user_id == "u1" else None

    def find_or_create_from_identity(self, identity: AuthIdentity):
        return User("u2", identity.email, identity.display_name, identity.avatar_url, identity.provider)


class StorageStub:
    def __init__(self):
        self.uploads = []
        self.signed = {}
        self.removed = []

    def upload(self, path: str, content: bytes, content_type: str) -> None:
        self.uploads.append((path, content, content_type))

    def download(self, path: str) -> bytes:
        return b""

    def remove_many(self, paths: list[str]) -> None:
        self.removed.append(paths)

    def create_signed_url(self, path: str, expires_in_seconds: int) -> str | None:
        return self.signed.get(path, f"signed:{path}:{expires_in_seconds}")


class BookRepoStub:
    def __init__(self):
        self.books = {}

    def create(self, book: Book) -> None:
        self.books[(book.id, book.user_id)] = book

    def get_by_id(self, book_id: str, user_id: str):
        return self.books.get((book_id, user_id))

    def list_by_user(self, user_id: str):
        return [book for (_, uid), book in self.books.items() if uid == user_id]

    def update_metadata(self, book_id: str, user_id: str, metadata: BookMetadata):
        book = self.get_by_id(book_id, user_id)
        if not book:
            return None
        updated = Book(
            id=book.id,
            user_id=book.user_id,
            storage_path=book.storage_path,
            metadata=metadata,
            ingestion=book.ingestion,
            cover_path=book.cover_path,
            created_at=book.created_at,
        )
        self.books[(book_id, user_id)] = updated
        return updated

    def update_cover_path(self, book_id: str, cover_path: str) -> None:
        for key, book in list(self.books.items()):
            if book.id == book_id:
                self.books[key] = Book(
                    id=book.id,
                    user_id=book.user_id,
                    storage_path=book.storage_path,
                    metadata=book.metadata,
                    ingestion=book.ingestion,
                    cover_path=cover_path,
                    created_at=book.created_at,
                )

    def update_ingestion(self, book_id: str, ingestion: IngestionInfo) -> None:
        for key, book in list(self.books.items()):
            if book.id == book_id:
                self.books[key] = Book(
                    id=book.id,
                    user_id=book.user_id,
                    storage_path=book.storage_path,
                    metadata=book.metadata,
                    ingestion=ingestion,
                    cover_path=book.cover_path,
                    created_at=book.created_at,
                )

    def delete(self, book_id: str, user_id: str) -> None:
        self.books.pop((book_id, user_id), None)


class ChunkRepoStub:
    def __init__(self, chunks=None):
        self.deleted = []
        self.before = chunks or []
        self.similar = chunks or []

    def delete_by_book(self, book_id: str) -> None:
        self.deleted.append(book_id)

    def replace_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        self.before = chunks

    def find_before_position(self, book_id: str, position_char: int):
        return self.before

    def search_similar(self, **kwargs):
        return self.similar


class PositionRepoStub:
    def __init__(self):
        self.deleted = []
        self.positions = {}

    def save(self, position: ReadingPosition) -> None:
        self.positions[(position.user_id, position.book_id)] = position

    def get(self, user_id: str, book_id: str):
        return self.positions.get((user_id, book_id))

    def delete(self, user_id: str, book_id: str) -> None:
        self.deleted.append((user_id, book_id))


class CacheStub:
    def __init__(self, cached=None):
        self.cached = cached
        self.set_calls = []

    def make_key(self, book_id: str, position_char: int, level: int) -> str:
        return f"{book_id}:{position_char}:{level}"

    def get(self, cache_key: str):
        return self.cached

    def set(self, cache_key: str, summary: str, ttl_seconds: int = 86400):
        self.set_calls.append((cache_key, summary, ttl_seconds))

    def invalidate_book(self, book_id: str) -> None:
        pass


class LLMStub:
    provider_name = "stub"
    recap_model = "stub-model"
    embedding_model = "stub-embedding"

    def recap(self, text_window: str, level: int) -> str:
        return f"{level}:{text_window}"

    def embed(self, text: str):
        return [0.1, 0.2]

    def embed_batch(self, texts: list[str]):
        return [[0.1, 0.2] for _ in texts]


class UsageLogStub:
    def __init__(self):
        self.calls = []

    def log_summary_generation(self, **kwargs):
        self.calls.append(kwargs)


def test_auth_application_service_returns_user_dto():
    service = AuthApplicationService(UserRepoStub())

    user = service.get_user("u1")

    assert user is not None
    assert user.id == "u1"
    assert user.auth_provider == "google"


def test_book_service_returns_book_dtos():
    books = BookRepoStub()
    storage = StorageStub()
    chunks = ChunkRepoStub()
    positions = PositionRepoStub()
    service = BookService(books, storage, chunks, positions)

    created = service.create_book("u1", b"epub", "application/epub+zip", "Title", "Author")
    listed = service.list_books("u1")
    status = service.get_book_status(created.id, "u1")

    assert created.title == "Title"
    assert listed[0].author == "Author"
    assert status is not None
    assert status.status == "ready"


def test_book_service_delete_removes_dependencies():
    books = BookRepoStub()
    storage = StorageStub()
    chunks = ChunkRepoStub()
    positions = PositionRepoStub()
    service = BookService(books, storage, chunks, positions)
    created = service.create_book("u1", b"epub", "application/epub+zip", "Title", "Author")

    deleted = service.delete_book(created.id, "u1")

    assert deleted is not None
    assert chunks.deleted == [created.id]
    assert positions.deleted == [("u1", created.id)]


def test_recap_service_returns_cached_result_without_logging():
    resolver = WindowResolverService(ChunkRepoStub([]), LLMStub())
    cache = CacheStub(cached="cached summary")
    usage_logs = UsageLogStub()
    service = RecapService(resolver, cache, LLMStub(), usage_logs)

    result = service.generate("u1", "b1", 10, 1)

    assert result.cached is True
    assert result.summary == "cached summary"
    assert usage_logs.calls == []


def test_recap_service_generates_summary_and_logs_usage():
    chunks = [
        BookChunk("b1", 0, 0, 0, 10, 5, "alpha"),
        BookChunk("b1", 0, 1, 10, 20, 5, "beta"),
    ]
    resolver = WindowResolverService(ChunkRepoStub(chunks), LLMStub())
    cache = CacheStub()
    usage_logs = UsageLogStub()
    service = RecapService(resolver, cache, LLMStub(), usage_logs)

    result = service.generate("u1", "b1", 20, 1)

    assert result.cached is False
    assert result.summary == "1:alpha\n\nbeta"
    assert usage_logs.calls
