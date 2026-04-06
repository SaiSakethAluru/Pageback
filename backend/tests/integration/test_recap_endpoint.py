from pathlib import Path
from uuid import uuid4

import pytest

from app.services.ingestion import ingest_book


@pytest.mark.integration
def test_recap_endpoint_uses_cache(authenticated_test_client, supabase_client, cleanup_book, test_user_id):
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    user_id = test_user_id
    book_id = str(uuid4())
    storage_path = f"{user_id}/{book_id}/original.epub"

    cleanup_book(book_id)
    supabase_client.storage.from_("books").upload(
        storage_path,
        fixture.read_bytes(),
        {"content-type": "application/epub+zip"},
    )
    supabase_client.table("books").insert(
        {"id": book_id, "user_id": user_id, "storage_path": storage_path, "ingestion_status": "pending"}
    ).execute()

    ingest_book(book_id, user_id, storage_path)

    first = authenticated_test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 1},
    ).get_json()
    second = authenticated_test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 1},
    ).get_json()
    level_two = authenticated_test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 2},
    ).get_json()

    assert first["summary"]
    assert first["cached"] is False
    assert second["cached"] is True
    assert len(level_two["summary"]) >= len(first["summary"])
