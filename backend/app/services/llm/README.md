# `services/llm/`

This folder defines the LLM abstraction layer used by the backend.

## Contents

- `__init__.py`: package marker.
- `base_provider.py`: abstract interface for recap and embedding providers.
- `openai_provider.py`: OpenAI implementation used by default.
- `claude_provider.py`: stubbed Claude provider.
- `gemini_provider.py`: stubbed Gemini provider.
- `provider_factory.py`: selects the active provider based on config.

## Notes

- All providers expose the same three methods: `recap`, `embed`, and `embed_batch`.
- Only the OpenAI provider is implemented today.
