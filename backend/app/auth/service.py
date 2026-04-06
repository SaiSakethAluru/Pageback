class AuthService:
    def __init__(self) -> None:
        from app.bootstrap import get_container

        self._service = get_container().auth_service

    def get_user(self, user_id: str) -> dict | None:
        user = self._service.get_user(user_id)
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "auth_provider": user.auth_provider,
        }

    def find_or_create_user(self, identity) -> dict:
        user = self._service.find_or_create_user(identity)
        return {
            "id": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "auth_provider": user.auth_provider,
        }
