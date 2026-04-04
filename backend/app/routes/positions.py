from flask import Blueprint, jsonify, request

from app.auth import current_user_id, require_auth
from app.bootstrap import get_container

positions_bp = Blueprint("positions", __name__, url_prefix="/api/v1/positions")


@positions_bp.put("/<book_id>")
@require_auth
def upsert_position(book_id: str):
    payload = request.get_json(silent=True) or {}
    user_id = current_user_id()
    position_cfi = payload.get("position_cfi")
    position_char = payload.get("position_char")

    if position_cfi is None:
        return jsonify({"error": "Missing required field: position_cfi"}), 400
    if position_char is None:
        return jsonify({"error": "Missing required field: position_char"}), 400

    try:
        position_char = int(position_char)
    except (TypeError, ValueError):
        return jsonify({"error": "position_char must be an integer"}), 400

    try:
        get_container().position_service.save(user_id, book_id, position_cfi, position_char)
    except Exception as exc:
        return jsonify({"error": f"Could not save reading position: {exc}"}), 500

    return jsonify({"success": True})


@positions_bp.get("/<book_id>")
@require_auth
def get_position(book_id: str):
    user_id = current_user_id()
    position = get_container().position_service.get(user_id, book_id)
    if not position:
        return jsonify({"position_cfi": None, "position_char": 0})

    return jsonify(
        {
            "book_id": position.book_id,
            "user_id": position.user_id,
            "position_cfi": position.position_cfi,
            "position_char": position.position_char,
            "updated_at": position.updated_at,
        }
    )
