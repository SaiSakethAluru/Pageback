from flask import Blueprint, jsonify, request
from supabase import Client, create_client

from app.auth import current_user_id, require_auth
from app.services import recap_cache, window_resolver
from app.services.llm import provider_factory
from app.utils import token_counter
from config import Config

recap_bp = Blueprint("recap", __name__, url_prefix="/api/v1/recap")

LLM_USAGE_TABLE = "llm_usage"


def _supabase() -> Client:
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)


def _estimated_cost_usd(input_tokens: int, output_tokens: int, model: str) -> float:
    if model == "gpt-4o-mini":
        return round((input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60), 6)
    return 0.0


def _log_token_usage(user_id: str, provider_name: str, model_name: str, text_window: str, summary: str) -> None:
    input_tokens = token_counter.count(text_window)
    output_tokens = token_counter.count(summary)
    _supabase().table(LLM_USAGE_TABLE).insert(
        {
            "user_id": user_id,
            "provider": provider_name,
            "model": model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": _estimated_cost_usd(input_tokens, output_tokens, model_name),
        }
    ).execute()


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

    cache_key = recap_cache.make_key(book_id, position_char, level)
    cached = recap_cache.get(cache_key)
    if cached:
        return jsonify({"summary": cached, "level": level, "cached": True})

    text_window = window_resolver.resolve(book_id, position_char, level)
    provider = provider_factory.get_provider()
    summary = provider.recap(text_window, level)

    recap_cache.set(cache_key, summary)
    _log_token_usage(user_id, provider.provider_name, provider.recap_model, text_window, summary)

    return jsonify({"summary": summary, "level": level, "cached": False})


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
