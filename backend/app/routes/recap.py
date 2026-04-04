from flask import Blueprint, jsonify, request

from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.services.llm import provider_factory
from config import Config

recap_bp = Blueprint("recap", __name__, url_prefix="/api/v1/recap")


@recap_bp.post("/")
@require_auth
def generate_recap():
    payload = request.get_json(silent=True) or {}
    book_id = (payload.get("book_id") or "").strip()
    user_id = current_user_id()
    position_char = payload.get("position_char")
    level = payload.get("level")

    if not book_id:
        return jsonify({"error": "Missing required field: book_id"}), 400
    if position_char is None:
        return jsonify({"error": "Missing required field: position_char"}), 400
    if level is None:
        return jsonify({"error": "Missing required field: level"}), 400

    try:
        position_char = int(position_char)
    except (TypeError, ValueError):
        return jsonify({"error": "position_char must be an integer"}), 400
    try:
        level = int(level)
    except (TypeError, ValueError):
        return jsonify({"error": "level must be an integer between 1 and 5"}), 400
    if level < 1 or level > 5:
        return jsonify({"error": "level must be an integer between 1 and 5"}), 400

    result = get_container().recap_service.generate(user_id, book_id, position_char, level)
    return jsonify(result)


@recap_bp.get("/levels")
def get_levels():
    levels = []
    for index, token_budget in enumerate(Config.RECAP_TOKEN_BUDGETS, start=1):
        levels.append(
            {
                "level": index,
                "token_budget": token_budget,
                "output_instruction": Config.RECAP_OUTPUT_INSTRUCTIONS[index - 1],
            }
        )
    # TODO: Add SSE streaming once core flow is stable.
    return jsonify(levels)
