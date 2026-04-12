from app.application.auth.service import AuthApplicationService
from app.application.books.ingestion_service import BookIngestionService
from app.application.books.ingestion_workflow import BookIngestionWorkflow
from app.application.books.lifecycle_workflow import BookLifecycleWorkflow
from app.application.books.service import BookService
from app.application.recap.service import RecapService, WindowResolverService
from app.domain.auth.models import AuthIdentity, User
from app.domain.books.models import Book, BookChunk, BookMetadata, IngestionInfo, IngestionRequest
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
        self.ingestion_requests = {}
        self.model_config_id = "model-config-123"
        self.ingestion_history = []

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
        self.ingestion_history.append((book_id, ingestion))
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

    def create_ingestion_request(self, request: IngestionRequest) -> None:
        self.ingestion_requests[request.id] = request

    def update_ingestion_request(self, request_id: str, ingestion: IngestionInfo) -> None:
        request = self.ingestion_requests[request_id]
        self.ingestion_requests[request_id] = IngestionRequest(
            id=request.id,
            book_id=request.book_id,
            user_id=request.user_id,
            book_title=request.book_title,
            model_config_id=request.model_config_id,
            status=ingestion.status,
            progress=ingestion.progress,
            step=ingestion.step,
            error_message=ingestion.error,
            error_type=request.error_type,
            log_path=request.log_path,
            celery_task_id=request.celery_task_id,
            control_status=request.control_status,
            embedded_chunks=request.embedded_chunks,
            total_chunks=request.total_chunks,
            embedded_tokens=request.embedded_tokens,
            total_tokens=request.total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )

    def mark_ingestion_request_started(self, request_id: str) -> None:
        pass

    def mark_ingestion_request_finished(
        self,
        request_id: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        request = self.ingestion_requests[request_id]
        self.ingestion_requests[request_id] = IngestionRequest(
            id=request.id,
            book_id=request.book_id,
            user_id=request.user_id,
            book_title=request.book_title,
            model_config_id=request.model_config_id,
            status=status,
            progress=request.progress,
            step=request.step,
            error_type=error_type,
            error_message=error_message,
            log_path=request.log_path,
            celery_task_id=request.celery_task_id,
            control_status=request.control_status,
            embedded_chunks=request.embedded_chunks,
            total_chunks=request.total_chunks,
            embedded_tokens=request.embedded_tokens,
            total_tokens=request.total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )

    def update_ingestion_request_task_id(self, request_id: str, task_id: str | None) -> None:
        request = self.ingestion_requests[request_id]
        self.ingestion_requests[request_id] = IngestionRequest(
            id=request.id,
            book_id=request.book_id,
            user_id=request.user_id,
            book_title=request.book_title,
            model_config_id=request.model_config_id,
            status=request.status,
            progress=request.progress,
            step=request.step,
            error_type=request.error_type,
            error_message=request.error_message,
            log_path=request.log_path,
            celery_task_id=task_id,
            control_status=request.control_status,
            embedded_chunks=request.embedded_chunks,
            total_chunks=request.total_chunks,
            embedded_tokens=request.embedded_tokens,
            total_tokens=request.total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )

    def get_latest_ingestion_request(self, book_id: str, user_id: str):
        matching = [
            request
            for request in self.ingestion_requests.values()
            if request.book_id == book_id and request.user_id == user_id
        ]
        return matching[-1] if matching else None

    def get_ingestion_request(self, request_id: str):
        return self.ingestion_requests.get(request_id)

    def list_ingestion_requests_by_user(self, user_id: str, statuses: list[str] | None = None):
        return [
            request
            for request in self.ingestion_requests.values()
            if request.user_id == user_id and (not statuses or request.status in statuses)
        ]

    def update_ingestion_request_progress(
        self,
        request_id: str,
        embedded_chunks: int,
        total_chunks: int,
        embedded_tokens: int,
        total_tokens: int,
    ) -> None:
        request = self.ingestion_requests[request_id]
        self.ingestion_requests[request_id] = IngestionRequest(
            id=request.id,
            book_id=request.book_id,
            user_id=request.user_id,
            book_title=request.book_title,
            model_config_id=request.model_config_id,
            status=request.status,
            progress=request.progress,
            step=request.step,
            error_type=request.error_type,
            error_message=request.error_message,
            log_path=request.log_path,
            celery_task_id=request.celery_task_id,
            control_status=request.control_status,
            embedded_chunks=embedded_chunks,
            total_chunks=total_chunks,
            embedded_tokens=embedded_tokens,
            total_tokens=total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )

    def update_ingestion_request_control(self, request_id: str, control_status: str, status: str | None = None) -> None:
        request = self.ingestion_requests[request_id]
        self.ingestion_requests[request_id] = IngestionRequest(
            id=request.id,
            book_id=request.book_id,
            user_id=request.user_id,
            book_title=request.book_title,
            model_config_id=request.model_config_id,
            status=status or request.status,
            progress=request.progress,
            step=request.step,
            error_type=request.error_type,
            error_message=request.error_message,
            log_path=request.log_path,
            celery_task_id=request.celery_task_id,
            control_status=control_status,
            embedded_chunks=request.embedded_chunks,
            total_chunks=request.total_chunks,
            embedded_tokens=request.embedded_tokens,
            total_tokens=request.total_tokens,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )

    def ensure_model_config(self, provider: str, recap_model: str, embedding_model: str) -> str:
        self.model_config = (provider, recap_model, embedding_model)
        return self.model_config_id

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

    def upsert_for_book(self, book_id: str, chunks: list[BookChunk]) -> None:
        by_key = {(chunk.chapter_index, chunk.chunk_index): chunk for chunk in self.before}
        for chunk in chunks:
            by_key[(chunk.chapter_index, chunk.chunk_index)] = chunk
        self.before = list(by_key.values())

    def find_embedded_keys(self, book_id: str):
        return {
            (chunk.chapter_index, chunk.chunk_index)
            for chunk in self.before
            if chunk.book_id == book_id and chunk.embedding is not None
        }

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
        self.invalidated = book_id


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


class QueueStub:
    def __init__(self):
        self.calls = []

    def enqueue(self, request_id: str, book_id: str, user_id: str, storage_path: str):
        self.calls.append((request_id, book_id, user_id, storage_path))
        return "task-123"


class MetadataExtractorStub:
    def extract(self, file_bytes: bytes, filename: str | None = None):
        class Result:
            title = "Extracted Title"
            author = "Extracted Author"
            cover_bytes = b"cover"
            cover_content_type = "image/jpeg"
            cover_extension = ".jpg"

        return Result()


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


def test_ingestion_workflow_enqueues_background_job_and_updates_status():
    books = BookRepoStub()
    storage = StorageStub()
    chunks = ChunkRepoStub()
    positions = PositionRepoStub()
    book_service = BookService(books, storage, chunks, positions)
    created = book_service.create_book("u1", b"epub", "application/epub+zip", "Title", "Author")
    queue = QueueStub()
    workflow = BookIngestionWorkflow(book_service, queue, LLMStub())

    book, result = workflow.start(created.id, "u1")

    assert book is not None
    assert result.request_id
    assert result.status == "processing"
    assert result.task_id == "task-123"
    assert queue.calls == [(result.request_id, created.id, "u1", created.storage_path)]
    assert books.ingestion_requests[result.request_id].book_title == "Title"
    assert books.ingestion_requests[result.request_id].model_config_id == "model-config-123"


def test_book_lifecycle_workflow_uploads_book_and_cover():
    books = BookRepoStub()
    storage = StorageStub()
    chunks = ChunkRepoStub()
    positions = PositionRepoStub()
    book_service = BookService(books, storage, chunks, positions)
    cache = CacheStub()
    workflow = BookLifecycleWorkflow(book_service, MetadataExtractorStub(), cache)

    result = workflow.upload_book("u1", b"epub", "sample.epub", "application/epub+zip")

    assert result.status == "ready"
    assert len(storage.uploads) == 2


def test_ingestion_embedding_progress_tracks_completed_chunks():
    books = BookRepoStub()
    storage = StorageStub()
    chunks_repo = ChunkRepoStub()
    positions = PositionRepoStub()
    book_service = BookService(books, storage, chunks_repo, positions)
    created = book_service.create_book("u1", b"epub", "application/epub+zip", "Title", "Author")
    request = IngestionRequest(
        id="req-1",
        book_id=created.id,
        user_id="u1",
        book_title="Title",
        model_config_id="model-config-123",
        status="processing",
        progress=35,
        step="chunked (150 chunks)",
    )
    books.create_ingestion_request(request)
    books.update_ingestion(
        created.id,
        IngestionInfo(status="processing", progress=35, step="chunked (150 chunks)", request_id="req-1"),
    )

    service = BookIngestionService(books, storage, chunks_repo, LLMStub(), None)
    source_chunks = [
        BookChunk(created.id, 0, index, index * 10, index * 10 + 10, 5, f"chunk-{index}")
        for index in range(150)
    ]

    service._embed_chunks("req-1", created.id, source_chunks)

    embedding_updates = [
        ingestion
        for book_id, ingestion in books.ingestion_history
        if book_id == created.id and ingestion.step and ingestion.step.startswith("embedding (")
    ]
    assert embedding_updates
    assert embedding_updates[0].step == "embedding (100/150)"
    assert embedding_updates[0].progress == 75
    assert not any(
        ingestion.step == "embedding (0/150)" and ingestion.progress and ingestion.progress > 35
        for ingestion in embedding_updates
    )


def test_book_lifecycle_workflow_invalidates_cache_on_delete():
    books = BookRepoStub()
    storage = StorageStub()
    chunks = ChunkRepoStub()
    positions = PositionRepoStub()
    book_service = BookService(books, storage, chunks, positions)
    created = book_service.create_book("u1", b"epub", "application/epub+zip", "Title", "Author")
    cache = CacheStub()
    workflow = BookLifecycleWorkflow(book_service, MetadataExtractorStub(), cache)

    result = workflow.delete_book(created.id, "u1")

    assert result is not None
    assert cache.invalidated == created.id
