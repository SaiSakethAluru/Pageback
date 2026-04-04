from __future__ import annotations

from app.domain.auth.models import AuthIdentity, User
from app.domain.auth.repositories import UserRepository


class AuthApplicationService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def get_user(self, user_id: str) -> User | None:
        return self._users.get_by_id(user_id)

    def find_or_create_user(self, identity: AuthIdentity) -> User:
        return self._users.find_or_create_from_identity(identity)
