from __future__ import annotations


class ApplicationError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApplicationError):
    status_code = 400


class AuthenticationError(ApplicationError):
    status_code = 401


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 409


class InfrastructureError(ApplicationError):
    status_code = 500
