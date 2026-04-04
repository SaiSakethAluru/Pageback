from pathlib import Path
from uuid import uuid4

import pytest

from app.services.ingestion import ingest_book


@pytest.mark.integration
def test_ingestion_pipeline_stores_chunks_and_embeddings(supabase_client, cleanup_book, test_user_id):
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

    chunk_rows = supabase_client.table("book_chunks").select("*").eq("book_id", book_id).execute().data
    book_row = supabase_client.table("books").select("ingestion_status").eq("id", book_id).single().execute().data

    assert chunk_rows
    assert all(row["embedding"] for row in chunk_rows)
    assert book_row["ingestion_status"] == "complete"
