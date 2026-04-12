from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BookDTO:
    id: str
    title: str | None
    author: str | None
    cover_path: str | None
    cover_url: str | None
    ingestion_status: str
    ingestion_progress: int | None
    ingestion_step: str | None
    ingestion_error: str | None
    created_at: str | None


@dataclass(frozen=True)
class BookFileDTO:
    id: str
    user_id: str
    storage_path: str
    title: str | None
    author: str | None
    cover_path: str | None
    ingestion_status: str
    ingestion_progress: int | None
    ingestion_step: str | None
    ingestion_error: str | None
    created_at: str | None


@dataclass(frozen=True)
class BookStatusDTO:
    id: str
    status: str
    progress: int | None
    step: str | None
    error: str | None
    error_type: str | None = None
    request_id: str | None = None
    log_path: str | None = None
    model_config_id: str | None = None


@dataclass(frozen=True)
class IngestionRequestDTO:
    id: str
    book_id: str
    book_title: str | None
    status: str
    control_status: str
    progress: int | None
    step: str | None
    error_type: str | None
    error_message: str | None
    embedded_chunks: int
    total_chunks: int | None
    embedded_tokens: int
    total_tokens: int | None
    created_at: str | None
    started_at: str | None
    completed_at: str | None
