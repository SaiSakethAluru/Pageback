from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from supabase import create_client

from app import create_app


load_dotenv(Path(__file__).resolve().parents[2] / ".env.test")


def _require_integration_env() -> None:
    required = [
        "OPENAI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "FLASK_SECRET_KEY",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing integration env vars: {', '.join(missing)}")


@pytest.fixture
def test_app():
    _require_integration_env()
    app = create_app()
    app.config.update(TESTING=True)
    return app


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture
def supabase_client():
    _require_integration_env()
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


@pytest.fixture
def cleanup_book(supabase_client):
    created_book_ids: list[str] = []

    def register(book_id: str) -> None:
        created_book_ids.append(book_id)

    yield register

    for book_id in created_book_ids:
        supabase_client.table("book_chunks").delete().eq("book_id", book_id).execute()
        supabase_client.table("books").delete().eq("id", book_id).execute()
