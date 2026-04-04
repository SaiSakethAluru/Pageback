import logging

from flask import Blueprint, jsonify, request

from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.services import recap_cache
from app.services.llm import provider_factory
from app.tasks.ingestion_tasks import ingest_book_task
from app.utils.epub_metadata import extract_epub_metadata
from config import Config

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

logger = logging.getLogger(__name__)

EPUB_MIME_TYPE = "application/epub+zip"


@books_bp.post("/upload")
@require_auth
def upload_book():
    user_id = current_user_id()
    file = request.files.get("file")

    if file is None:
        return jsonify({"error": "Missing required form field: file"}), 400

    if file.mimetype != EPUB_MIME_TYPE:
        return (
            jsonify(
                {
                    "error": (
                        f"Invalid MIME type '{file.mimetype}'. "
                        f"Only '{EPUB_MIME_TYPE}' is supported."
                    )
                }
            ),
            400,
        )

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return jsonify({"error": f"File size exceeds {Config.MAX_UPLOAD_SIZE_MB}MB limit"}), 400

    file_bytes = file.read()
    extracted = extract_epub_metadata(file_bytes, file.filename)
    book_service = get_container().book_service
    book = book_service.create_book(
        user_id=user_id,
        file_bytes=file_bytes,
        content_type=EPUB_MIME_TYPE,
        title=extracted["title"],
        author=extracted["author"],
    )

    cover_path = _store_cover(
        user_id=user_id,
        book_id=book.id,
        cover_bytes=extracted["cover_bytes"],
        content_type=extracted["cover_content_type"],
        extension=extracted["cover_extension"],
    )
    if cover_path:
        book_service.update_cover_path(book.id, cover_path)

    return jsonify({"book_id": book.id, "status": "ready"})


@books_bp.get("/<book_id>/status")
@require_auth
def get_book_status(book_id: str):
    user_id = current_user_id()
    book = get_container().book_service.get_book(book_id, user_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    provider = provider_factory.get_provider()
    return jsonify(
        {
            "book_id": book_id,
            "status": book.ingestion.status,
            "progress": book.ingestion.progress,
            "step": book.ingestion.step,
            "error": book.ingestion.error,
            "llm": {
                "provider": provider.provider_name,
                "recap_model": provider.recap_model,
                "embedding_model": provider.embedding_model,
            },
        }
    )


@books_bp.post("/<book_id>/ingestion/start")
@require_auth
def start_ingestion(book_id: str):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    background = bool(payload.get("background", True))

    book = get_container().book_service.get_book(book_id, user_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    get_container().book_service.update_ingestion_status(
        book_id,
        status="processing",
        progress=0,
        step="queued",
        error=None,
    )

    if not background:
        from app.services.ingestion import ingest_book

        ingest_book(book_id=book_id, user_id=user_id, storage_path=book.storage_path)
        return jsonify({"book_id": book_id, "status": "complete"})

    task = ingest_book_task.delay(book_id, user_id, book.storage_path)
    return jsonify({"book_id": book_id, "status": "processing", "celery_task_id": task.id})


@books_bp.get("/")
@require_auth
def list_books():
    user_id = current_user_id()
    book_service = get_container().book_service
    books = [
        book_service.serialize(
            book,
            cover_url=book_service.create_signed_cover_url(book.cover_path),
        )
        for book in book_service.list_books(user_id)
    ]
    return jsonify(books)


@books_bp.patch("/<book_id>/metadata")
@require_auth
def update_book_metadata(book_id: str):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    title = _normalize_metadata_text(payload.get("title"))
    author = _normalize_metadata_text(payload.get("author"))

    updated = get_container().book_service.update_metadata(book_id, user_id, title, author)
    if not updated:
        return jsonify({"error": "Book not found"}), 404

    return jsonify(
        {
            "book_id": book_id,
            "title": updated.metadata.title,
            "author": updated.metadata.author,
        }
    )


@books_bp.delete("/<book_id>")
@require_auth
def delete_book(book_id: str):
    user_id = current_user_id()
    book = get_container().book_service.get_book(book_id, user_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    try:
        get_container().book_service.delete_book(book_id, user_id)
        recap_cache.invalidate_book(book_id)
    except Exception as exc:
        logger.exception("Failed to delete book_id=%s user_id=%s", book_id, user_id)
        return jsonify({"error": f"Could not delete book: {exc}"}), 500

    return jsonify({"book_id": book_id, "deleted": True})


@books_bp.get("/<book_id>/file-url")
@require_auth
def get_book_file_url(book_id: str):
    user_id = current_user_id()
    signed_url = get_container().book_service.create_signed_book_url(book_id, user_id)
    if not signed_url:
        return jsonify({"error": "Book not found"}), 404
    return jsonify({"signed_url": signed_url})


def _normalize_metadata_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _store_cover(
    user_id: str,
    book_id: str,
    cover_bytes: object,
    content_type: object,
    extension: object,
) -> str | None:
    if not isinstance(cover_bytes, bytes) or not cover_bytes:
        return None

    suffix = str(extension or ".jpg")
    if not suffix.startswith("."):
        suffix = f".{suffix}"

    cover_path = f"{user_id}/{book_id}/cover{suffix}"
    get_container().book_service.upload_cover(
        cover_path,
        cover_bytes,
        str(content_type or "image/jpeg"),
    )
    return cover_path
