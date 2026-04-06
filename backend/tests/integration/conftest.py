from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parents[2] / ".env.test")
if os.getenv("OPENAI_API_KEY"):
    os.environ["LLM_PROVIDER"] = "openai"
if os.getenv("GEMINI_EMBEDDING_MODEL") == "embedding-001":
    os.environ["GEMINI_EMBEDDING_MODEL"] = "gemini-embedding-001"

from app import create_app
from app.auth.session import AUTH_SESSION_KEY


def _require_integration_env() -> None:
    required = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "FLASK_SECRET_KEY",
    ]
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    if llm_provider != "openai":
        pytest.skip("Integration coverage currently requires LLM_PROVIDER=openai because the test schema uses 1536-d embeddings.")
    required.append("OPENAI_API_KEY")
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


@pytest.fixture
def test_user_id(supabase_client):
    user_id = "00000000-0000-0000-0000-000000000000"
    existing = supabase_client.table("app_users").select("id").eq("id", user_id).limit(1).execute().data or []
    if not existing:
        supabase_client.table("app_users").insert(
            {
                "id": user_id,
                "email": "integration@example.com",
                "display_name": "Integration User",
                "avatar_url": None,
                "auth_provider": "test",
                "provider_subject": f"test-{user_id}",
            }
        ).execute()
    return user_id


@pytest.fixture
def authenticated_test_client(test_client, test_user_id):
    with test_client.session_transaction() as session:
        session[AUTH_SESSION_KEY] = test_user_id
    return test_client
