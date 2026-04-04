from flask import Blueprint, jsonify, request

from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.services.llm import provider_factory
from app.interfaces.http.mappers import parse_recap_request, serialize_recap_levels

recap_bp = Blueprint("recap", __name__, url_prefix="/api/v1/recap")


@recap_bp.post("/")
@require_auth
def generate_recap():
    user_id = current_user_id()
    recap_request = parse_recap_request(request.get_json(silent=True) or {})
    result = get_container().recap_service.generate(
        user_id,
        recap_request.book_id,
        recap_request.position_char,
        recap_request.level,
    )
    return jsonify(result)


@recap_bp.get("/levels")
def get_levels():
    return jsonify(serialize_recap_levels())
