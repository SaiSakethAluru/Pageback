# Backend

The backend is a Flask API that handles upload, ingestion, reading-position persistence, and spoiler-safe recap generation.

## Responsibilities

- validate environment configuration at startup
- accept EPUB uploads
- store original files in Supabase Storage
- parse and chunk book content
- generate embeddings for semantic retrieval
- resolve recap windows behind the user's reading position
- cache recap responses
- save and restore reading positions

## Structure

```text
backend/
  app/
    routes/      # HTTP endpoints
    services/    # ingestion, retrieval, caching, LLM providers
    utils/       # parsers and token counting
  tests/
  config.py
  run.py
  requirements.txt
```

## Main Endpoints

### `POST /api/v1/books/upload`

Uploads an EPUB, creates a `books` row, and kicks off ingestion in a background thread.

### `GET /api/v1/books/<book_id>/status`

Returns the current ingestion status.

### `GET /api/v1/books?user_id=...`

Returns a user's library.

### `PUT /api/v1/positions/<book_id>`

Upserts the saved reading position.

### `GET /api/v1/positions/<book_id>?user_id=...`

Returns the latest saved reading position.

### `POST /api/v1/recap/`

Generates or returns a cached recap for a given reading position and recap level.

### `GET /api/v1/recap/levels`

Returns recap-level configuration.

## Local Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Required Environment

- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `FLASK_SECRET_KEY`

Optional:

- `LLM_PROVIDER`
- `FLASK_ENV`
- `FRONTEND_URL`

## Testing

Unit tests:

```bash
pytest tests/unit/ -v
```

Integration tests:

```bash
cp .env .env.test
pytest tests/integration/ -v
```

## Design Notes

- Levels 1-2 use deterministic recent-chunk retrieval.
- Levels 3-5 use semantic retrieval through the Supabase `match_chunks` RPC.
- The spoiler fence is enforced by `end_char <= position_char`.
- The current cache is process-local and will not survive restarts.

## Production Caveats

- `threading.Thread` should be replaced with a proper queue worker.
- The service key is powerful; treat it like a secret.
- In-memory cache is suitable for local development, not horizontal scale.
