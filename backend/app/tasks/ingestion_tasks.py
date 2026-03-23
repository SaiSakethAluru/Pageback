from __future__ import annotations

import logging

from app.celery_app import celery_app
from app.services import ingestion


logger = logging.getLogger(__name__)


@celery_app.task(name="ingestion.ingest_book")
def ingest_book_task(book_id: str, user_id: str, storage_path: str) -> None:
    """
    Runs the ingestion pipeline in a Celery worker process.
    """
    logger.info("Starting ingestion task book_id=%s user_id=%s", book_id, user_id)
    ingestion.ingest_book(book_id=book_id, user_id=user_id, storage_path=storage_path)

