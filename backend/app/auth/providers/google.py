from __future__ import annotations

import secrets
from urllib.parse import urlencode

import google.auth.transport.requests
import google.oauth2.id_token
import requests
from flask import session

from app.auth.models import AuthIdentity
from app.auth.providers.base import OAuthProvider
from config import Config

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleOAuthProvider(OAuthProvider):
    name = "google"
    state_session_key = "oauth_state_google"
    nonce_session_key = "oauth_nonce_google"

    def begin_auth(self) -> str:
        session[self.state_session_key] = secrets.token_urlsafe(24)
        session[self.nonce_session_key] = secrets.token_urlsafe(24)

        params = {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "redirect_uri": Config.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": session[self.state_session_key],
            "nonce": session[self.nonce_session_key],
            "access_type": "offline",
            "include_granted_scopes": "true",
            # TODO: Extend auth providers to support GitHub, Apple, and email/password.
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    def authenticate_callback(self, request_args) -> AuthIdentity:
        state = request_args.get("state")
        if not state or state != session.pop(self.state_session_key, None):
            raise ValueError("Invalid OAuth state")

        code = request_args.get("code")
        if not code:
            raise ValueError("Missing OAuth code")

        tokens = self._exchange_code_for_tokens(code)
        claims = self._verify_google_identity(tokens["id_token"])

        return AuthIdentity(
            provider=self.name,
            provider_subject=claims["sub"],
            email=claims.get("email"),
            display_name=claims.get("name"),
            avatar_url=claims.get("picture"),
            email_verified=claims.get("email_verified") is True,
        )

    def _exchange_code_for_tokens(self, code: str) -> dict:
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": Config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def _verify_google_identity(self, id_token: str) -> dict:
        claims = google.oauth2.id_token.verify_oauth2_token(
            id_token,
            google.auth.transport.requests.Request(),
            Config.GOOGLE_CLIENT_ID,
        )
        expected_nonce = session.pop(self.nonce_session_key, None)
        if not expected_nonce or claims.get("nonce") != expected_nonce:
            raise ValueError("Invalid OAuth nonce")
        if claims.get("email_verified") is not True:
            raise ValueError("Google account email is not verified")
        return claims
