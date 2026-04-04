from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.application.auth.service import AuthApplicationService
from app.application.books.service import BookService
from app.application.positions.service import ReadingPositionService
from app.infrastructure.db.supabase import create_supabase_client
from app.infrastructure.db.supabase.repositories import (
    SupabaseBookRepository,
    SupabaseChunkRepository,
    SupabaseReadingPositionRepository,
    SupabaseUserRepository,
)
from app.infrastructure.storage import SupabaseBookStorage


@dataclass(frozen=True)
class ApplicationContainer:
    auth_service: AuthApplicationService
    book_service: BookService
    position_service: ReadingPositionService


@lru_cache(maxsize=1)
def get_container() -> ApplicationContainer:
    book_repository = SupabaseBookRepository(create_supabase_client)
    position_repository = SupabaseReadingPositionRepository(create_supabase_client)
    chunk_repository = SupabaseChunkRepository(create_supabase_client)
    user_repository = SupabaseUserRepository(create_supabase_client)
    book_storage = SupabaseBookStorage(create_supabase_client)
    return ApplicationContainer(
        auth_service=AuthApplicationService(user_repository),
        book_service=BookService(book_repository, book_storage, chunk_repository, position_repository),
        position_service=ReadingPositionService(position_repository),
    )
