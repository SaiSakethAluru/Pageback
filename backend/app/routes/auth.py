from __future__ import annotations

import logging

from flask import Blueprint, jsonify, redirect, request

from app.application.errors import AuthenticationError
from app.auth import current_user_id, login_user, logout_user
from app.auth.providers import GoogleOAuthProvider
from app.bootstrap import get_container
from app.interfaces.http.errors import error_response
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

google_provider = GoogleOAuthProvider()
logger = logging.getLogger(__name__)


def _frontend_url(path: str = "") -> str:
    base = Config.FRONTEND_URL.rstrip("/")
    if not path:
        return base
    return f"{base}{path if path.startswith('/') else f'/{path}'}"


@auth_bp.get("/google/start")
def start_google_auth():
    return redirect(google_provider.begin_auth())


@auth_bp.get("/google/callback")
def finish_google_auth():
    error = request.args.get("error")
    if error:
        return redirect(_frontend_url(f"/login?error={error}"))

    try:
        identity = google_provider.authenticate_callback(request.args)
        user = get_container().auth_service.find_or_create_user(identity)
        login_user(user.id)
    except Exception:
        logger.exception("Google OAuth callback failed")
        return redirect(_frontend_url("/login?error=oauth_failed"))

    return redirect(_frontend_url("/library"))


@auth_bp.get("/me")
def get_current_user():
    user_id = current_user_id()
    if not user_id:
        return error_response(AuthenticationError("Authentication required"))

    user = get_container().auth_service.get_user(user_id)
    if not user:
        logout_user()
        return error_response(AuthenticationError("Authentication required"))

    return jsonify(
        {
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "auth_provider": user.auth_provider,
            }
        }
    )


@auth_bp.post("/logout")
def logout():
    logout_user()
    return jsonify({"success": True})


@auth_bp.get("/dev-login")
def dev_login():
    if Config.FLASK_ENV != "development":
        return error_response(AuthenticationError("Dev login is only available in development mode"))

    user_id = request.args.get("user_id", "1c7d0909-e663-47c7-a44b-522a89c5ca2c")
    user = get_container().auth_service.get_user(user_id)
    if not user:
        user = get_container().auth_service.get_user("b153ea33-f145-4fd6-ae81-93be8ca8f70c")
    if not user:
        return error_response(AuthenticationError("No development user found"))

    login_user(user.id)
    redirect_target = request.args.get("redirect", "/library")
    return redirect(_frontend_url(redirect_target))

