from __future__ import annotations

from supabase import Client, create_client

from config import Config


def create_supabase_client() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
