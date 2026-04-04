from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.application.books.ingestion_service import BookIngestionService
from app.application.books.ingestion_workflow import BookIngestionWorkflow
from app.application.books.lifecycle_workflow import BookLifecycleWorkflow
from app.application.auth.service import AuthApplicationService
from app.application.books.service import BookService
from app.application.positions.service import ReadingPositionService
from app.application.recap.service import RecapService, WindowResolverService
from app.application.system.service import SystemInfoService
from app.infrastructure.db.supabase import create_supabase_client
from app.infrastructure.db.supabase.repositories import (
    SupabaseBookRepository,
    SupabaseChunkRepository,
    SupabaseReadingPositionRepository,
    SupabaseUsageLogRepository,
    SupabaseUserRepository,
)
from app.infrastructure.cache import InMemoryRecapCache
from app.infrastructure.llm import get_llm_gateway
from app.infrastructure.parsers import EpubMetadataExtractor, get_parser_factory
from app.infrastructure.storage import SupabaseBookStorage
from app.infrastructure.tasks import CeleryBookIngestionQueue


@dataclass(frozen=True)
class ApplicationContainer:
    auth_service: AuthApplicationService
    book_service: BookService
    book_lifecycle_workflow: BookLifecycleWorkflow
    ingestion_service: BookIngestionService
    ingestion_workflow: BookIngestionWorkflow
    position_service: ReadingPositionService
    recap_service: RecapService
    system_service: SystemInfoService
    window_resolver: WindowResolverService


@lru_cache(maxsize=1)
def get_container() -> ApplicationContainer:
    book_repository = SupabaseBookRepository(create_supabase_client)
    position_repository = SupabaseReadingPositionRepository(create_supabase_client)
    chunk_repository = SupabaseChunkRepository(create_supabase_client)
    user_repository = SupabaseUserRepository(create_supabase_client)
    usage_log_repository = SupabaseUsageLogRepository(create_supabase_client)
    book_storage = SupabaseBookStorage(create_supabase_client)
    llm_gateway = get_llm_gateway()
    parser_factory = get_parser_factory()
    ingestion_queue = CeleryBookIngestionQueue()
    book_service = BookService(book_repository, book_storage, chunk_repository, position_repository)
    ingestion_service = BookIngestionService(
        book_repository,
        book_storage,
        chunk_repository,
        llm_gateway,
        parser_factory,
    )
    window_resolver = WindowResolverService(chunk_repository, llm_gateway)
    return ApplicationContainer(
        auth_service=AuthApplicationService(user_repository),
        book_service=book_service,
        book_lifecycle_workflow=BookLifecycleWorkflow(
            book_service,
            EpubMetadataExtractor(),
            InMemoryRecapCache(),
        ),
        ingestion_service=ingestion_service,
        ingestion_workflow=BookIngestionWorkflow(
            book_service,
            ingestion_queue,
            ingestion_service,
        ),
        position_service=ReadingPositionService(position_repository),
        recap_service=RecapService(window_resolver, InMemoryRecapCache(), llm_gateway, usage_log_repository),
        system_service=SystemInfoService(llm_gateway),
        window_resolver=window_resolver,
    )
