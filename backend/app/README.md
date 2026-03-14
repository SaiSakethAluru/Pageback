# `app/`

This is the main backend application package.

## Contents

- `__init__.py`: Flask app factory, CORS setup, and blueprint registration.
- `routes/`: HTTP endpoints for books, reading positions, and recaps.
- `services/`: ingestion pipeline, retrieval logic, cache layer, and LLM providers.
- `utils/`: parsing and token-counting helpers used by services.

## Notes

- Most request/response logic lives in `routes/`.
- Most business logic lives in `services/`.
- Shared low-level helpers live in `utils/`.
