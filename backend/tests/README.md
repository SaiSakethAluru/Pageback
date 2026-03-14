# `tests/`

This folder contains backend test code and fixtures.

## Contents

- `__init__.py`: package marker.
- `fixtures/`: sample test assets used by parsers and integration tests.
- `unit/`: isolated tests for parsers, token counting, cache, and retrieval logic.
- `integration/`: tests that exercise real Supabase and OpenAI-backed flows.

## Notes

- Unit tests are intended to run without external services.
- Integration tests require `.env.test` with working credentials.
