import logging
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.application.errors import ApplicationError, InfrastructureError
from app.auth import current_user_id, require_auth
from app.bootstrap import get_container
from app.interfaces.http.mappers import parse_recap_request, serialize_recap_levels

recap_bp = Blueprint("recap", __name__, url_prefix="/api/v1/recap")
logger = logging.getLogger(__name__)


@recap_bp.post("/")
@recap_bp.post("")
@require_auth
def generate_recap():
    user_id = current_user_id()
    recap_request = parse_recap_request(request.get_json(silent=True) or {})
    try:
        result = get_container().recap_service.generate(
            user_id,
            recap_request.book_id,
            recap_request.position_char,
            recap_request.level,
            position_cfi=recap_request.position_cfi,
        )
    except ApplicationError:
        raise
    except Exception as exc:
        logger.exception(
            "Recap request failed user_id=%s book_id=%s position_char=%s level=%s",
            user_id,
            recap_request.book_id,
            recap_request.position_char,
            recap_request.level,
        )
        raise InfrastructureError(
            "The recap request failed. Check the backend server logs for the traceback."
        ) from exc
    return jsonify(asdict(result))


@recap_bp.get("/levels")
def get_levels():
    return jsonify(serialize_recap_levels())
