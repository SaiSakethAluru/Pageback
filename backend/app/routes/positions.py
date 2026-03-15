from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from app.auth import current_user_id, require_auth
from config import Config

positions_bp = Blueprint("positions", __name__, url_prefix="/api/v1/positions")

POSITIONS_TABLE = "reading_positions"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


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

    sb = _supabase()
    sb.table(POSITIONS_TABLE).upsert(
        {
            "user_id": user_id,
            "book_id": book_id,
            "position_cfi": position_cfi,
            "position_char": position_char,
        },
        on_conflict="user_id,book_id",
    ).execute()

    return jsonify({"success": True})


@positions_bp.get("/<book_id>")
@require_auth
def get_position(book_id: str):
    user_id = current_user_id()
    sb = _supabase()
    response = (
        sb.table(POSITIONS_TABLE)
        .select("user_id, book_id, position_cfi, position_char, updated_at")
        .eq("user_id", user_id)
        .eq("book_id", book_id)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        return jsonify({"position_cfi": None, "position_char": 0})

    row = rows[0]
    return jsonify(
        {
            "book_id": row.get("book_id"),
            "user_id": row.get("user_id"),
            "position_cfi": row.get("position_cfi"),
            "position_char": row.get("position_char"),
            "updated_at": row.get("updated_at"),
        }
    )
