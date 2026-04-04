from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookMetadata:
    title: str | None
    author: str | None


@dataclass(frozen=True)
class IngestionInfo:
    status: str
    progress: int | None = None
    step: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class Book:
    id: str
    user_id: str
    storage_path: str
    metadata: BookMetadata
    ingestion: IngestionInfo
    cover_path: str | None = None
    created_at: str | None = None
