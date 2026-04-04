from __future__ import annotations

from app.application.errors import ValidationError
from app.domain.books.parsing import (
    BookFileMetadataExtractor,
    BookParser,
    ExtractedBookMetadata,
    ParserFactory,
)
from app.utils.epub_metadata import extract_epub_metadata
from app.utils.epub_parser import EpubParser
from app.utils.pdf_parser import PdfParser


class DefaultParserFactory(ParserFactory):
    def get_parser(self, filepath: str) -> BookParser:
        lowered = filepath.lower()
        if lowered.endswith(".epub"):
            return EpubParser(filepath)
        if lowered.endswith(".pdf"):
            return PdfParser(filepath)
        raise ValidationError(f"Unsupported file type: {filepath}")


class EpubMetadataExtractor(BookFileMetadataExtractor):
    def extract(self, file_bytes: bytes, filename: str | None = None) -> ExtractedBookMetadata:
        extracted = extract_epub_metadata(file_bytes, filename)
        return ExtractedBookMetadata(
            title=extracted["title"],
            author=extracted["author"],
            cover_bytes=extracted["cover_bytes"] if isinstance(extracted["cover_bytes"], bytes) else None,
            cover_content_type=(
                str(extracted["cover_content_type"]) if extracted["cover_content_type"] is not None else None
            ),
            cover_extension=str(extracted["cover_extension"]) if extracted["cover_extension"] is not None else None,
        )


def get_parser_factory() -> ParserFactory:
    return DefaultParserFactory()
