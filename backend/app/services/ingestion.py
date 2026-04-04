def ingest_book(book_id: str, user_id: str, storage_path: str) -> None:
    from app.bootstrap import get_container

    get_container().ingestion_service.ingest_book(book_id=book_id, user_id=user_id, storage_path=storage_path)
