from __future__ import annotations

import uuid
from datetime import datetime, timezone

from supabase import Client, create_client

from app.auth.models import AuthIdentity
from config import Config

USERS_TABLE = "app_users"


class AuthService:
    def __init__(self) -> None:
        self._supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)

    def get_user(self, user_id: str) -> dict | None:
        response = (
            self._supabase.table(USERS_TABLE)
            .select("id, email, display_name, avatar_url, auth_provider")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None
        return self._serialize_user(rows[0])

    def find_or_create_user(self, identity: AuthIdentity) -> dict:
        login_timestamp = datetime.now(timezone.utc).isoformat()
        response = (
            self._supabase.table(USERS_TABLE)
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
            self._supabase.table(USERS_TABLE).update(
                {
                    **payload,
                    "last_login_at": login_timestamp,
                }
            ).eq("id", user["id"]).execute()
            return self._serialize_user({**user, **payload, "auth_provider": identity.provider})

        user = {
            "id": str(uuid.uuid4()),
            **payload,
            "auth_provider": identity.provider,
            "provider_subject": identity.provider_subject,
            "last_login_at": login_timestamp,
        }
        self._supabase.table(USERS_TABLE).insert(user).execute()
        return self._serialize_user(user)

    @staticmethod
    def _serialize_user(user: dict) -> dict:
        return {
            "id": user.get("id"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "avatar_url": user.get("avatar_url"),
            "auth_provider": user.get("auth_provider"),
        }
