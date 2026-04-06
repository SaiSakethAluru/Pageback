from __future__ import annotations

from app.domain.auth.models import AuthIdentity, User
from app.domain.auth.repositories import UserRepository
from app.application.auth.dto import UserDTO


class AuthApplicationService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def get_user(self, user_id: str) -> UserDTO | None:
        user = self._users.get_by_id(user_id)
        if not user:
            return None
        return self._to_dto(user)

    def find_or_create_user(self, identity: AuthIdentity) -> UserDTO:
        return self._to_dto(self._users.find_or_create_from_identity(identity))

    @staticmethod
    def _to_dto(user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            auth_provider=user.auth_provider,
        )
