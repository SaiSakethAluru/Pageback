from __future__ import annotations

from dataclasses import dataclass

from app.application.books.dto import BookFileDTO
from app.application.books.service import BookService
from app.domain.books.parsing import BookFileMetadataExtractor
from app.domain.recap.models import RecapCache


@dataclass(frozen=True)
class UploadBookResultDTO:
    book_id: str
    status: str


@dataclass(frozen=True)
class DeleteBookResultDTO:
    book_id: str
    deleted: bool


class BookLifecycleWorkflow:
    def __init__(
        self,
        books: BookService,
        metadata_extractor: BookFileMetadataExtractor,
        recap_cache: RecapCache,
    ) -> None:
        self._books = books
        self._metadata_extractor = metadata_extractor
        self._recap_cache = recap_cache

    def upload_book(
        self,
        user_id: str,
        file_bytes: bytes,
        filename: str | None,
        content_type: str,
    ) -> UploadBookResultDTO:
        extracted = self._metadata_extractor.extract(file_bytes, filename)
        book = self._books.create_book(
            user_id=user_id,
            file_bytes=file_bytes,
            content_type=content_type,
            title=extracted.title,
            author=extracted.author,
        )
        cover_path = self._store_cover(
            user_id=user_id,
            book_id=book.id,
            cover_bytes=extracted.cover_bytes,
            content_type=extracted.cover_content_type,
            extension=extracted.cover_extension,
        )
        if cover_path:
            self._books.update_cover_path(book.id, cover_path)
        return UploadBookResultDTO(book_id=book.id, status="ready")

    def delete_book(self, book_id: str, user_id: str) -> DeleteBookResultDTO | None:
        deleted = self._books.delete_book(book_id, user_id)
        if not deleted:
            return None
        self._recap_cache.invalidate_book(book_id)
        return DeleteBookResultDTO(book_id=book_id, deleted=True)

    def get_book(self, book_id: str, user_id: str) -> BookFileDTO | None:
        return self._books.get_book(book_id, user_id)

    def _store_cover(
        self,
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
        self._books.upload_cover(
            cover_path,
            cover_bytes,
            str(content_type or "image/jpeg"),
        )
        return cover_path
