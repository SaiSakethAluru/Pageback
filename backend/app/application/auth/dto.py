from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserDTO:
    id: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    auth_provider: str | None
