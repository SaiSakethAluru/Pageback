from __future__ import annotations

from abc import ABC, abstractmethod

from app.auth.models import AuthIdentity


class OAuthProvider(ABC):
    name: str

    @abstractmethod
    def begin_auth(self) -> str:
        pass

    @abstractmethod
    def authenticate_callback(self, request_args) -> AuthIdentity:
        pass
