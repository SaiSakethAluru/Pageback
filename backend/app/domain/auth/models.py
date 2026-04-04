from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthIdentity:
    provider: str
    provider_subject: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    email_verified: bool


@dataclass(frozen=True)
class User:
    id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    auth_provider: str | None
