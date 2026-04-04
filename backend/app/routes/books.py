import logging

from flask import Blueprint, jsonify, request

from app.application.errors import InfrastructureError, NotFoundError
from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.interfaces.http.errors import error_response
from app.interfaces.http.mappers import parse_book_metadata_update, parse_upload_request
from app.services import recap_cache
from app.services.llm import provider_factory
from app.tasks.ingestion_tasks import ingest_book_task

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

logger = logging.getLogger(__name__)


@books_bp.post("/upload")
@require_auth
def upload_book():
    user_id = current_user_id()
    upload_request = parse_upload_request(request.files.get("file"))
    extracted = get_container().book_metadata_extractor.extract(
        upload_request.file_bytes,
        upload_request.filename,
    )
    book_service = get_container().book_service
    book = book_service.create_book(
        user_id=user_id,
        file_bytes=upload_request.file_bytes,
        content_type=upload_request.content_type,
        title=extracted.title,
        author=extracted.author,
    )

    cover_path = _store_cover(
        user_id=user_id,
        book_id=book.id,
        cover_bytes=extracted.cover_bytes,
        content_type=extracted.cover_content_type,
        extension=extracted.cover_extension,
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
        return error_response(NotFoundError("Book not found"))

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
        return error_response(NotFoundError("Book not found"))
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
    metadata_request = parse_book_metadata_update(request.get_json(silent=True) or {})

    updated = get_container().book_service.update_metadata(
        book_id,
        user_id,
        metadata_request.title,
        metadata_request.author,
    )
    if not updated:
        return error_response(NotFoundError("Book not found"))

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
        return error_response(NotFoundError("Book not found"))

    try:
        get_container().book_service.delete_book(book_id, user_id)
        recap_cache.invalidate_book(book_id)
    except Exception as exc:
        logger.exception("Failed to delete book_id=%s user_id=%s", book_id, user_id)
        return error_response(InfrastructureError(f"Could not delete book: {exc}"))

    return jsonify({"book_id": book_id, "deleted": True})


@books_bp.get("/<book_id>/file-url")
@require_auth
def get_book_file_url(book_id: str):
    user_id = current_user_id()
    signed_url = get_container().book_service.create_signed_book_url(book_id, user_id)
    if not signed_url:
        return error_response(NotFoundError("Book not found"))
    return jsonify({"signed_url": signed_url})


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
