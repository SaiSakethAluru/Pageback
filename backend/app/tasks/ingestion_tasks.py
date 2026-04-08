from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator
from pathlib import Path

from app.celery_app import celery_app
from app.services import ingestion
from config import Config


logger = logging.getLogger(__name__)


@celery_app.task(name="ingestion.ingest_book")
def ingest_book_task(request_id: str, book_id: str, user_id: str, storage_path: str) -> None:
    """
    Runs the ingestion pipeline in a Celery worker process.
    """
    log_path = Path(Config.INGESTION_LOG_DIR) / f"{request_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with _task_log_context(log_path):
        logger.info(
            "Starting ingestion task request_id=%s book_id=%s user_id=%s",
            request_id,
            book_id,
            user_id,
        )
        ingestion.ingest_book(
            request_id=request_id,
            book_id=book_id,
            user_id=user_id,
            storage_path=storage_path,
        )


@contextlib.contextmanager
def _task_log_context(log_path: Path) -> Iterator[None]:
    root_logger = logging.getLogger()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root_logger.addHandler(handler)
    with log_path.open("a", encoding="utf-8") as log_file:
        try:
            with contextlib.redirect_stdout(log_file), contextlib.redirect_stderr(log_file):
                yield
        finally:
            root_logger.removeHandler(handler)
            handler.close()
