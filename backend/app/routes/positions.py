from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.application.errors import InfrastructureError
from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.interfaces.http.errors import error_response
from app.interfaces.http.mappers import parse_position_payload, serialize_position

positions_bp = Blueprint("positions", __name__, url_prefix="/api/v1/positions")


@positions_bp.put("/<book_id>")
@require_auth
def upsert_position(book_id: str):
    user_id = current_user_id()
    position_request = parse_position_payload(request.get_json(silent=True) or {})

    try:
        get_container().position_service.save(
            user_id,
            book_id,
            position_request.position_cfi,
            position_request.position_char,
        )
    except Exception as exc:
        return error_response(InfrastructureError(f"Could not save reading position: {exc}"))

    return jsonify({"success": True})


@positions_bp.get("/<book_id>")
@require_auth
def get_position(book_id: str):
    user_id = current_user_id()
    position = get_container().position_service.get(user_id, book_id)
    if not position:
        return jsonify(serialize_position(position))
    return jsonify(asdict(position))
