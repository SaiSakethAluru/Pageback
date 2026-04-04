from __future__ import annotations

from collections.abc import Callable

from supabase import Client

from app.domain.books.repositories import BookStorage

BOOKS_BUCKET = "books"


class SupabaseBookStorage(BookStorage):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def upload(self, path: str, content: bytes, content_type: str) -> None:
        self._client_factory().storage.from_(BOOKS_BUCKET).upload(path, content, {"content-type": content_type})

    def download(self, path: str) -> bytes:
        return self._client_factory().storage.from_(BOOKS_BUCKET).download(path)

    def remove_many(self, paths: list[str]) -> None:
        if not paths:
            return
        self._client_factory().storage.from_(BOOKS_BUCKET).remove(paths)

    def create_signed_url(self, path: str, expires_in_seconds: int) -> str | None:
        signed = self._client_factory().storage.from_(BOOKS_BUCKET).create_signed_url(path, expires_in_seconds)
        return signed.get("signedURL")
