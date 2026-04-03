from __future__ import annotations

import mimetypes
import tempfile
from pathlib import Path

from ebooklib import ITEM_IMAGE, epub


def extract_epub_metadata(file_bytes: bytes, filename: str | None = None) -> dict[str, object]:
    filepath = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as temp_file:
            temp_file.write(file_bytes)
            filepath = temp_file.name

        book = epub.read_epub(filepath)
        title = _first_metadata_value(book.get_metadata("DC", "title"))
        author = _first_metadata_value(book.get_metadata("DC", "creator"))
        cover = _extract_cover(book)

        if not title and filename:
            title = Path(filename).stem

        return {
            "title": title,
            "author": author,
            "cover_bytes": cover["bytes"] if cover else None,
            "cover_content_type": cover["content_type"] if cover else None,
            "cover_extension": cover["extension"] if cover else None,
        }
    finally:
        if filepath:
            Path(filepath).unlink(missing_ok=True)


def _first_metadata_value(entries: list[tuple[str, dict]]) -> str | None:
    for value, _attrs in entries:
        normalized = (value or "").strip()
        if normalized:
            return normalized
    return None


def _extract_cover(book) -> dict[str, object] | None:
    cover_item_id = None
    cover_metadata = book.get_metadata("OPF", "cover")
    if cover_metadata:
        _value, attrs = cover_metadata[0]
        cover_item_id = attrs.get("content")

    if cover_item_id:
        item = book.get_item_with_id(cover_item_id)
        if item is not None:
            payload = _cover_payload(item.get_content(), item.media_type, item.get_name())
            if payload:
                return payload

    for item in book.get_items():
        if item.get_type() != ITEM_IMAGE:
            continue
        payload = _cover_payload(item.get_content(), item.media_type, item.get_name())
        if payload and "cover" in (item.get_name() or "").lower():
            return payload

    for item in book.get_items():
        if item.get_type() != ITEM_IMAGE:
            continue
        payload = _cover_payload(item.get_content(), item.media_type, item.get_name())
        if payload:
            return payload

    return None


def _cover_payload(image_bytes: bytes, content_type: str | None, name: str | None) -> dict[str, object] | None:
    if not image_bytes:
        return None

    resolved_content_type = content_type or mimetypes.guess_type(name or "")[0] or "image/jpeg"
    extension = mimetypes.guess_extension(resolved_content_type) or Path(name or "cover.jpg").suffix or ".jpg"
    if extension == ".jpe":
        extension = ".jpg"

    return {
        "bytes": image_bytes,
        "content_type": resolved_content_type,
        "extension": extension,
    }
