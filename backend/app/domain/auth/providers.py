from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.auth.models import AuthIdentity


class OAuthProvider(ABC):
    name: str

    @abstractmethod
    def begin_auth(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def authenticate_callback(self, request_args) -> AuthIdentity:
        raise NotImplementedError
