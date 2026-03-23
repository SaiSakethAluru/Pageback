# Backend

The backend is a Flask API that handles upload, ingestion, reading-position persistence, and spoiler-safe recap generation.

## Responsibilities

- validate environment configuration at startup
- own the user session and Google OAuth flow
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

Uploads an EPUB, creates a `books` row, and marks it as `ready` (LLM processing is opt-in).

### `POST /api/v1/books/<book_id>/ingestion/start`

Starts the ingestion workflow (chunking + embeddings) either in the foreground or via Celery background execution.

### `GET /api/v1/books/<book_id>/status`

Returns the current ingestion status.

### `GET /api/v1/books/`

Returns the authenticated user's library.

### `PUT /api/v1/positions/<book_id>`

Upserts the saved reading position.

### `GET /api/v1/positions/<book_id>`

Returns the latest saved reading position.

### `GET /api/v1/auth/google/start`

Starts the Google OAuth flow.

### `GET /api/v1/auth/me`

Returns the currently authenticated user.

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
../scripts/start_backend.sh
```

Redis is required for background ingestion. In another terminal, start Redis:

```bash
redis-server
```

When you start the backend via `../scripts/start_backend.sh`, the Celery worker is started automatically (unless `START_CELERY_WORKER=false`).

## Required Environment

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `FLASK_SECRET_KEY`

Optional:

- `BACKEND_PORT`
- `LLM_PROVIDER`
- `OPENAI_API_KEY` (required when `LLM_PROVIDER=openai`)
- `GEMINI_API_KEY` (required when `LLM_PROVIDER=gemini`)
- `GEMINI_RECAP_MODEL`
- `GEMINI_EMBEDDING_MODEL`
- `REDIS_URL` (required for Celery broker/result backend)
- `FLASK_ENV`
- `FRONTEND_URL`
- `GOOGLE_REDIRECT_URI`
- `SESSION_COOKIE_NAME`
- `SESSION_COOKIE_SAMESITE`
- `SESSION_COOKIE_SECURE`

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
- Google is the only auth provider wired today, but the session model is app-owned and can be extended later.

## Supabase Schema Notes

The ingestion pipeline publishes progress and errors so the reader UI can show status while background ingestion runs.

Add these optional columns to the `books` table:

```sql
alter table public.books
  add column if not exists ingestion_progress integer,
  add column if not exists ingestion_step text,
  add column if not exists ingestion_error text;
```

Embedding note (important):
- The Supabase `book_chunks.embedding` vector dimension (and the `match_chunks` RPC) must match the embedding model configured via `*_EMBEDDING_MODEL`.
- For example, `gemini-embedding-001` uses 3072-dimensional vectors, while the default OpenAI embedding model uses a different dimension.

## Production Caveats
- `threading.Thread` has been replaced with Celery for background ingestion.
- The service key is powerful; treat it like a secret.
- In-memory cache is suitable for local development, not horizontal scale.
