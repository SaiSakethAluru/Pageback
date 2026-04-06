from __future__ import annotations

from dataclasses import dataclass

from app.application.errors import ValidationError
from config import Config


@dataclass(frozen=True)
class RecapRequest:
    book_id: str
    position_char: int
    level: int


def parse_recap_request(payload: dict) -> RecapRequest:
    book_id = (payload.get("book_id") or "").strip()
    position_char = payload.get("position_char")
    level = payload.get("level")

    if not book_id:
        raise ValidationError("Missing required field: book_id")
    if position_char is None:
        raise ValidationError("Missing required field: position_char")
    if level is None:
        raise ValidationError("Missing required field: level")

    try:
        resolved_position_char = int(position_char)
    except (TypeError, ValueError) as exc:
        raise ValidationError("position_char must be an integer") from exc
    try:
        resolved_level = int(level)
    except (TypeError, ValueError) as exc:
        raise ValidationError("level must be an integer between 1 and 5") from exc
    if resolved_level < 1 or resolved_level > 5:
        raise ValidationError("level must be an integer between 1 and 5")

    return RecapRequest(book_id=book_id, position_char=resolved_position_char, level=resolved_level)


def serialize_recap_levels() -> list[dict]:
    levels = []
    for index, token_budget in enumerate(Config.RECAP_TOKEN_BUDGETS, start=1):
        levels.append(
            {
                "level": index,
                "token_budget": token_budget,
                "output_instruction": Config.RECAP_OUTPUT_INSTRUCTIONS[index - 1],
            }
        )
    return levels
