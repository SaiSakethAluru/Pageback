from __future__ import annotations

from celery import Celery

from config import Config


celery_app = Celery(
    "pageback",
    broker=Config.CELERY_BROKER_URL,
    backend=Config.CELERY_RESULT_BACKEND,
)

# Keep tasks simple; we persist ingestion progress in Supabase rather than
# depending on Celery result storage.
celery_app.conf.update(
    task_ignore_result=True,
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_concurrency=Config.CELERY_WORKER_CONCURRENCY,
)

# Register tasks on worker startup.
import app.tasks.ingestion_tasks  # noqa: E402,F401
