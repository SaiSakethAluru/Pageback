from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.auth.models import AuthIdentity, User


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def find_or_create_from_identity(self, identity: AuthIdentity) -> User:
        raise NotImplementedError
