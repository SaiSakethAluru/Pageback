from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedBookMetadata:
    title: str | None
    author: str | None
    cover_bytes: bytes | None
    cover_content_type: str | None
    cover_extension: str | None


class BookParser(ABC):
    @abstractmethod
    def extract(self) -> list[dict]:
        raise NotImplementedError


class ParserFactory(ABC):
    @abstractmethod
    def get_parser(self, filepath: str) -> BookParser:
        raise NotImplementedError


class BookFileMetadataExtractor(ABC):
    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str | None = None) -> ExtractedBookMetadata:
        raise NotImplementedError
