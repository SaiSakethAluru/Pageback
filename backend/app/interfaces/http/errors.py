from __future__ import annotations

from flask import jsonify

from app.application.errors import ApplicationError


def error_response(error: ApplicationError):
    return jsonify({"error": error.message}), error.status_code
