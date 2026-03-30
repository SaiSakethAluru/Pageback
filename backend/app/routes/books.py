import logging
import uuid

from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from app.auth import current_user_id, require_auth
from app.services import recap_cache
from app.services.llm import provider_factory
from app.utils.epub_metadata import extract_epub_metadata
from config import Config
from app.tasks.ingestion_tasks import ingest_book_task

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

logger = logging.getLogger(__name__)

BOOKS_TABLE = "books"
BOOK_CHUNKS_TABLE = "book_chunks"
BOOKS_BUCKET = "books"
POSITIONS_TABLE = "reading_positions"
EPUB_MIME_TYPE = "application/epub+zip"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


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

    # TODO: Add ClamAV file scanning before ingestion.
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return jsonify({"error": f"File size exceeds {Config.MAX_UPLOAD_SIZE_MB}MB limit"}), 400

    book_id = str(uuid.uuid4())
    storage_path = f"{user_id}/{book_id}/original.epub"
    file_bytes = file.read()
    extracted = extract_epub_metadata(file_bytes, file.filename)

    sb = _supabase()
    sb.storage.from_(BOOKS_BUCKET).upload(
        storage_path,
        file_bytes,
        {"content-type": EPUB_MIME_TYPE},
    )

    sb.table(BOOKS_TABLE).insert(
        {
            "id": book_id,
            "user_id": user_id,
            "storage_path": storage_path,
            "title": extracted["title"],
            "author": extracted["author"],
            "ingestion_status": "ready",
        }
    ).execute()

    cover_path = _store_cover(
        sb=sb,
        user_id=user_id,
        book_id=book_id,
        cover_bytes=extracted["cover_bytes"],
        content_type=extracted["cover_content_type"],
        extension=extracted["cover_extension"],
    )
    if cover_path:
        _update_cover_path(sb, book_id, cover_path)

    return jsonify({"book_id": book_id, "status": "ready"})


@books_bp.get("/<book_id>/status")
@require_auth
def get_book_status(book_id: str):
    user_id = current_user_id()
    sb = _supabase()
    try:
        select_fields = "ingestion_status, ingestion_progress, ingestion_step, ingestion_error"
        response = (
            sb.table(BOOKS_TABLE)
            .select(select_fields)
            .eq("id", book_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception:
        response = (
            sb.table(BOOKS_TABLE)
            .select("ingestion_status")
            .eq("id", book_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    rows = response.data or []
    if not rows:
        return jsonify({"error": "Book not found"}), 404

    row = rows[0]
    ingestion_status = row.get("ingestion_status") or "ready"
    provider = provider_factory.get_provider()
    return jsonify(
        {
            "book_id": book_id,
            "status": ingestion_status,
            "progress": row.get("ingestion_progress"),
            "step": row.get("ingestion_step"),
            "error": row.get("ingestion_error"),
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

    sb = _supabase()
    response = (
        sb.table(BOOKS_TABLE)
        .select("storage_path")
        .eq("id", book_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return jsonify({"error": "Book not found"}), 404

    storage_path = rows[0]["storage_path"]

    # Initialize progress fields best-effort; if your schema doesn't include
    # them yet, we still want ingestion_status to work.
    try:
        sb.table(BOOKS_TABLE).update(
            {
                "ingestion_status": "processing",
                "ingestion_progress": 0,
                "ingestion_step": "queued",
                "ingestion_error": None,
            }
        ).eq("id", book_id).execute()
    except Exception:
        sb.table(BOOKS_TABLE).update({"ingestion_status": "processing"}).eq("id", book_id).execute()

    if not background:
        # Foreground option: run ingestion inline (the request will block).
        # Celery path is preferred for the "keep reading while processing" UX.
        from app.services.ingestion import ingest_book

        ingest_book(book_id=book_id, user_id=user_id, storage_path=storage_path)
        return jsonify({"book_id": book_id, "status": "complete"})

    task = ingest_book_task.delay(book_id, user_id, storage_path)
    return jsonify({"book_id": book_id, "status": "processing", "celery_task_id": task.id})


@books_bp.get("/")
@require_auth
def list_books():
    user_id = current_user_id()
    sb = _supabase()
    try:
        response = (
            sb.table(BOOKS_TABLE)
            .select(
                "id, title, author, cover_path, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        try:
            response = (
                sb.table(BOOKS_TABLE)
                .select("id, title, author, ingestion_status, created_at, ingestion_progress, ingestion_step, ingestion_error")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )
        except Exception:
            response = (
                sb.table(BOOKS_TABLE)
                .select("id, title, author, ingestion_status, created_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

    books = response.data or []
    for book in books:
        book["cover_url"] = _signed_cover_url(sb, book.get("cover_path"))
    return jsonify(books)


@books_bp.patch("/<book_id>/metadata")
@require_auth
def update_book_metadata(book_id: str):
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    title = _normalize_metadata_text(payload.get("title"))
    author = _normalize_metadata_text(payload.get("author"))

    response = (
        _supabase()
        .table(BOOKS_TABLE)
        .select("id")
        .eq("id", book_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return jsonify({"error": "Book not found"}), 404

    updated = (
        _supabase()
        .table(BOOKS_TABLE)
        .update({"title": title, "author": author})
        .eq("id", book_id)
        .eq("user_id", user_id)
        .execute()
    )
    data = (updated.data or [{}])[0]
    return jsonify(
        {
            "book_id": book_id,
            "title": data.get("title", title),
            "author": data.get("author", author),
        }
    )


@books_bp.delete("/<book_id>")
@require_auth
def delete_book(book_id: str):
    user_id = current_user_id()
    sb = _supabase()
    response = (
        sb.table(BOOKS_TABLE)
        .select("storage_path")
        .eq("id", book_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return jsonify({"error": "Book not found"}), 404

    storage_path = rows[0]["storage_path"]
    cover_path = _cover_path_for_book(sb, book_id, user_id)

    try:
        sb.storage.from_(BOOKS_BUCKET).remove([storage_path])
        if cover_path:
            sb.storage.from_(BOOKS_BUCKET).remove([cover_path])
        sb.table(BOOK_CHUNKS_TABLE).delete().eq("book_id", book_id).execute()
        sb.table(POSITIONS_TABLE).delete().eq("user_id", user_id).eq("book_id", book_id).execute()
        sb.table(BOOKS_TABLE).delete().eq("id", book_id).eq("user_id", user_id).execute()
        recap_cache.invalidate_book(book_id)
    except Exception as exc:
        logger.exception("Failed to delete book_id=%s user_id=%s", book_id, user_id)
        return jsonify({"error": f"Could not delete book: {exc}"}), 500

    return jsonify({"book_id": book_id, "deleted": True})


@books_bp.get("/<book_id>/file-url")
@require_auth
def get_book_file_url(book_id: str):
    user_id = current_user_id()
    response = (
        _supabase()
        .table(BOOKS_TABLE)
        .select("storage_path")
        .eq("id", book_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return jsonify({"error": "Book not found"}), 404

    signed = _supabase().storage.from_(BOOKS_BUCKET).create_signed_url(rows[0]["storage_path"], 3600)
    return jsonify({"signed_url": signed.get("signedURL")})


def _normalize_metadata_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _store_cover(
    sb: Client,
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
    sb.storage.from_(BOOKS_BUCKET).upload(
        cover_path,
        cover_bytes,
        {"content-type": str(content_type or "image/jpeg")},
    )
    return cover_path


def _update_cover_path(sb: Client, book_id: str, cover_path: str) -> None:
    try:
        sb.table(BOOKS_TABLE).update({"cover_path": cover_path}).eq("id", book_id).execute()
    except Exception:
        logger.debug("cover_path column missing; skipping cover_path update for book_id=%s", book_id)


def _signed_cover_url(sb: Client, cover_path: str | None) -> str | None:
    if not cover_path:
        return None
    try:
        signed = sb.storage.from_(BOOKS_BUCKET).create_signed_url(cover_path, 3600)
        return signed.get("signedURL")
    except Exception:
        return None


def _cover_path_for_book(sb: Client, book_id: str, user_id: str) -> str | None:
    try:
        response = (
            sb.table(BOOKS_TABLE)
            .select("cover_path")
            .eq("id", book_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
    except Exception:
        return None

    rows = response.data or []
    if not rows:
        return None
    cover_path = rows[0].get("cover_path")
    if isinstance(cover_path, str) and cover_path.strip():
        return cover_path
    return None
