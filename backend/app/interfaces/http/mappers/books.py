from __future__ import annotations

from dataclasses import dataclass

from app.application.errors import ValidationError
from config import Config

EPUB_MIME_TYPE = "application/epub+zip"


@dataclass(frozen=True)
class UploadBookRequest:
    file_bytes: bytes
    filename: str | None
    content_type: str


@dataclass(frozen=True)
class UpdateBookMetadataRequest:
    title: str | None
    author: str | None


def parse_upload_request(file) -> UploadBookRequest:
    if file is None:
        raise ValidationError("Missing required form field: file")

    if file.mimetype != EPUB_MIME_TYPE:
        raise ValidationError(
            f"Invalid MIME type '{file.mimetype}'. Only '{EPUB_MIME_TYPE}' is supported."
        )

    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > Config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"File size exceeds {Config.MAX_UPLOAD_SIZE_MB}MB limit")

    return UploadBookRequest(
        file_bytes=file.read(),
        filename=file.filename,
        content_type=EPUB_MIME_TYPE,
    )


def parse_book_metadata_update(payload: dict) -> UpdateBookMetadataRequest:
    return UpdateBookMetadataRequest(
        title=_normalize_metadata_text(payload.get("title")),
        author=_normalize_metadata_text(payload.get("author")),
    )


def _normalize_metadata_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
