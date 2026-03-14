# `services/`

This folder contains the backend business logic.

## Contents

- `__init__.py`: package marker.
- `ingestion.py`: orchestrates download, parsing, chunking, embedding, and chunk storage.
- `window_resolver.py`: retrieves spoiler-safe text windows for recap generation.
- `recap_cache.py`: in-memory recap cache with TTL support.
- `llm/`: provider interface and concrete LLM provider implementations.

## Notes

- `ingestion.py` is the main pipeline entry point after upload.
- `window_resolver.py` enforces the spoiler fence via `end_char <= position_char`.
- `recap_cache.py` is intentionally simple so it can later be swapped for Redis.
