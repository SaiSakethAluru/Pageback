import logging
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.application.chat.dto import ChatMessageDTO
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


@recap_bp.post("/contextual-lookup")
@require_auth
def contextual_lookup():
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    book_id = str(payload.get("book_id") or "").strip()
    term = str(payload.get("term") or "").strip()
    try:
        position_char = int(payload.get("position_char") or 0)
    except (ValueError, TypeError):
        position_char = 0
    position_cfi = payload.get("position_cfi")

    if not book_id:
        return jsonify({"error": "book_id is required"}), 400
    if not term:
        return jsonify({"error": "term is required"}), 400

    try:
        result = get_container().contextual_lookup_service.lookup(
            user_id=user_id,
            book_id=book_id,
            term=term,
            position_char=position_char,
            position_cfi=position_cfi,
        )
    except ApplicationError:
        raise
    except Exception as exc:
        logger.exception("Contextual lookup failed user_id=%s book_id=%s term=%s", user_id, book_id, term)
        raise InfrastructureError("Contextual lookup failed.") from exc

    return jsonify(asdict(result))


@recap_bp.post("/chat")
@require_auth
def book_chat():
    user_id = current_user_id()
    payload = request.get_json(silent=True) or {}
    book_id = str(payload.get("book_id") or "").strip()
    raw_messages = payload.get("messages") or []
    try:
        position_char = int(payload.get("position_char") or 0)
    except (ValueError, TypeError):
        position_char = 0
    position_cfi = payload.get("position_cfi")

    if not book_id:
        return jsonify({"error": "book_id is required"}), 400
    if not isinstance(raw_messages, list) or not raw_messages:
        return jsonify({"error": "messages must be a non-empty list"}), 400

    messages = [
        ChatMessageDTO(
            role=str(m.get("role") or "user"),
            content=str(m.get("content") or ""),
        )
        for m in raw_messages
        if isinstance(m, dict) and m.get("content")
    ]

    try:
        result = get_container().chat_service.chat(
            user_id=user_id,
            book_id=book_id,
            messages=messages,
            position_char=position_char,
            position_cfi=position_cfi,
        )
    except ApplicationError:
        raise
    except Exception as exc:
        logger.exception("Chat request failed user_id=%s book_id=%s", user_id, book_id)
        raise InfrastructureError("Chat request failed.") from exc

    return jsonify(asdict(result))
