from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChatMessageDTO:
    role: str  # "user" or "assistant"
    content: str


@dataclass(frozen=True)
class ChatRequestDTO:
    book_id: str
    messages: list[ChatMessageDTO]
    position_char: int = 0
    position_cfi: str | None = None


@dataclass(frozen=True)
class ChatResponseDTO:
    reply: str
    grounded: bool
