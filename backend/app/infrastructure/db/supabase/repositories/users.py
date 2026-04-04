from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from supabase import Client

from app.domain.auth.models import AuthIdentity, User
from app.domain.auth.repositories import UserRepository

USERS_TABLE = "app_users"


def _serialize_user(row: dict) -> User:
    return User(
        id=str(row.get("id")),
        email=row.get("email"),
        display_name=row.get("display_name"),
        avatar_url=row.get("avatar_url"),
        auth_provider=row.get("auth_provider"),
    )


class SupabaseUserRepository(UserRepository):
    def __init__(self, client_factory: Callable[[], Client]) -> None:
        self._client_factory = client_factory

    def get_by_id(self, user_id: str) -> User | None:
        response = (
            self._client_factory()
            .table(USERS_TABLE)
            .select("id, email, display_name, avatar_url, auth_provider")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return _serialize_user(rows[0])

    def find_or_create_from_identity(self, identity: AuthIdentity) -> User:
        login_timestamp = datetime.now(timezone.utc).isoformat()
        client = self._client_factory()
        response = (
            client.table(USERS_TABLE)
            .select("id, email, display_name, avatar_url, auth_provider")
            .eq("auth_provider", identity.provider)
            .eq("provider_subject", identity.provider_subject)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        payload = {
            "email": identity.email,
            "display_name": identity.display_name,
            "avatar_url": identity.avatar_url,
        }
        if rows:
            user = rows[0]
            client.table(USERS_TABLE).update(
                {
                    **payload,
                    "last_login_at": login_timestamp,
                }
            ).eq("id", user["id"]).execute()
            return _serialize_user({**user, **payload, "auth_provider": identity.provider})

        user = {
            "id": str(uuid.uuid4()),
            **payload,
            "auth_provider": identity.provider,
            "provider_subject": identity.provider_subject,
            "last_login_at": login_timestamp,
        }
        client.table(USERS_TABLE).insert(user).execute()
        return _serialize_user(user)
