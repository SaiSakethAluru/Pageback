import logging
import threading
import uuid

from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from app.auth import current_user_id, require_auth
from app.services import ingestion
from config import Config

books_bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

logger = logging.getLogger(__name__)

BOOKS_TABLE = "books"
BOOKS_BUCKET = "books"
EPUB_MIME_TYPE = "application/epub+zip"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


def _start_ingestion_thread(book_id: str, user_id: str, storage_path: str) -> None:
    # TODO: Replace ad-hoc threads with a proper job queue (Celery + Redis).
    worker = threading.Thread(
        target=ingestion.ingest_book,
        kwargs={"book_id": book_id, "user_id": user_id, "storage_path": storage_path},
        daemon=True,
    )
    worker.start()

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

    sb = _supabase()
    sb.storage.from_(BOOKS_BUCKET).upload(
        storage_path,
        file.read(),
        {"content-type": EPUB_MIME_TYPE},
    )

    sb.table(BOOKS_TABLE).insert(
        {
            "id": book_id,
            "user_id": user_id,
            "storage_path": storage_path,
            "ingestion_status": "pending",
        }
    ).execute()

    _start_ingestion_thread(book_id=book_id, user_id=user_id, storage_path=storage_path)

    return jsonify({"book_id": book_id, "status": "pending"})


@books_bp.get("/<book_id>/status")
@require_auth
def get_book_status(book_id: str):
    user_id = current_user_id()
    sb = _supabase()
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
    return jsonify({"book_id": book_id, "status": row["ingestion_status"]})


@books_bp.get("/")
@require_auth
def list_books():
    user_id = current_user_id()
    sb = _supabase()
    response = (
        sb.table(BOOKS_TABLE)
        .select("id, title, author, ingestion_status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return jsonify(response.data or [])


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
