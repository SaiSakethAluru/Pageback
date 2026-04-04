from __future__ import annotations

from dataclasses import dataclass

from app.application.errors import ValidationError
from app.domain.positions.models import ReadingPosition


@dataclass(frozen=True)
class PositionRequest:
    position_cfi: str
    position_char: int


def parse_position_payload(payload: dict) -> PositionRequest:
    position_cfi = payload.get("position_cfi")
    position_char = payload.get("position_char")

    if position_cfi is None:
        raise ValidationError("Missing required field: position_cfi")
    if position_char is None:
        raise ValidationError("Missing required field: position_char")

    try:
        resolved_position_char = int(position_char)
    except (TypeError, ValueError) as exc:
        raise ValidationError("position_char must be an integer") from exc

    return PositionRequest(position_cfi=str(position_cfi), position_char=resolved_position_char)


def serialize_position(position: ReadingPosition | None) -> dict:
    if not position:
        return {"position_cfi": None, "position_char": 0}

    return {
        "book_id": position.book_id,
        "user_id": position.user_id,
        "position_cfi": position.position_cfi,
        "position_char": position.position_char,
        "updated_at": position.updated_at,
    }
