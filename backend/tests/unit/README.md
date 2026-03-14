# `tests/unit/`

This folder contains unit tests for isolated backend modules.

## Contents

- `__init__.py`: package marker.
- `test_epub_parser.py`: verifies EPUB extraction and text cleanup.
- `test_token_counter.py`: verifies token counting behavior.
- `test_window_resolver.py`: verifies token budgets, spoiler fence, and semantic retrieval calls.
- `test_recap_cache.py`: verifies cache hit, miss, expiry, and key generation behavior.

## Notes

- These tests should not require live network services.
