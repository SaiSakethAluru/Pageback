from __future__ import annotations

from flask import Blueprint, jsonify, redirect, request

from app.auth import AuthService, current_user_id, login_user, logout_user
from app.auth.providers import GoogleOAuthProvider
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

auth_service = AuthService()
google_provider = GoogleOAuthProvider()


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
        user = auth_service.find_or_create_user(identity)
        login_user(user["id"])
    except Exception:
        return redirect(_frontend_url("/login?error=oauth_failed"))

    return redirect(_frontend_url("/library"))


@auth_bp.get("/me")
def get_current_user():
    user_id = current_user_id()
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    user = auth_service.get_user(user_id)
    if not user:
        logout_user()
        return jsonify({"error": "Authentication required"}), 401

    return jsonify({"user": user})


@auth_bp.post("/logout")
def logout():
    logout_user()
    return jsonify({"success": True})
