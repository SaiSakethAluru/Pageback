from __future__ import annotations

from functools import wraps

from flask import jsonify, session

AUTH_SESSION_KEY = "user_id"


def current_user_id() -> str | None:
    user_id = session.get(AUTH_SESSION_KEY)
    if isinstance(user_id, str) and user_id.strip():
        return user_id
    return None


def login_user(user_id: str) -> None:
    session.clear()
    session[AUTH_SESSION_KEY] = user_id


def logout_user() -> None:
    session.clear()


def require_auth(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        user_id = current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required"}), 401
        return view_func(*args, **kwargs)

    return wrapped
