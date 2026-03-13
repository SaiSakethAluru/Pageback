from __future__ import annotations

import tiktoken

_encoder_cache: dict[str, tiktoken.Encoding] = {}


def count(text: str, model: str = "gpt-4o-mini") -> int:
    encoder = _encoder_cache.get(model)
    if encoder is None:
        encoder = tiktoken.encoding_for_model(model)
        _encoder_cache[model] = encoder
    return len(encoder.encode(text))
