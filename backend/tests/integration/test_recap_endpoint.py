from pathlib import Path
from uuid import uuid4

import pytest

from app.services.ingestion import ingest_book


@pytest.mark.integration
def test_recap_endpoint_uses_cache(test_client, supabase_client, cleanup_book):
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "sample.epub"
    user_id = "00000000-0000-0000-0000-000000000000"
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

    first = test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 1},
    ).get_json()
    second = test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 1},
    ).get_json()
    level_two = test_client.post(
        "/api/v1/recap/",
        json={"book_id": book_id, "user_id": user_id, "position_char": 1000, "level": 2},
    ).get_json()

    assert first["summary"]
    assert first["cached"] is False
    assert second["cached"] is True
    assert len(level_two["summary"]) >= len(first["summary"])
