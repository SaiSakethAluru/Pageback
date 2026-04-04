from __future__ import annotations

from collections.abc import Callable

from supabase import Client

from app.domain.positions.models import ReadingPosition
from app.domain.positions.repositories import ReadingPositionRepository

POSITIONS_TABLE = "reading_positions"


class SupabaseReadingPositionRepository(ReadingPositionRepository):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def save(self, position: ReadingPosition) -> None:
        payload = {
            "user_id": position.user_id,
            "book_id": position.book_id,
            "position_cfi": position.position_cfi,
            "position_char": position.position_char,
        }
        client = self._client_factory()
        try:
            client.table(POSITIONS_TABLE).upsert(payload, on_conflict="user_id,book_id").execute()
            return
        except Exception:
            pass

        existing = (
            client.table(POSITIONS_TABLE)
            .select("user_id, book_id")
            .eq("user_id", position.user_id)
            .eq("book_id", position.book_id)
            .limit(1)
            .execute()
        )
        rows = existing.data or []
        if rows:
            (
                client.table(POSITIONS_TABLE)
                .update(
                    {
                        "position_cfi": position.position_cfi,
                        "position_char": position.position_char,
                    }
                )
                .eq("user_id", position.user_id)
                .eq("book_id", position.book_id)
                .execute()
            )
            return
        client.table(POSITIONS_TABLE).insert(payload).execute()

    def get(self, user_id: str, book_id: str) -> ReadingPosition | None:
        response = (
            self._client_factory()
            .table(POSITIONS_TABLE)
            .select("user_id, book_id, position_cfi, position_char, updated_at")
            .eq("user_id", user_id)
            .eq("book_id", book_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        row = rows[0]
        return ReadingPosition(
            user_id=str(row.get("user_id")),
            book_id=str(row.get("book_id")),
            position_cfi=str(row.get("position_cfi")),
            position_char=int(row.get("position_char") or 0),
            updated_at=row.get("updated_at"),
        )

    def delete(self, user_id: str, book_id: str) -> None:
        self._client_factory().table(POSITIONS_TABLE).delete().eq("user_id", user_id).eq("book_id", book_id).execute()
