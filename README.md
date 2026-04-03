# PageBack

PageBack is an AI-assisted ebook reader that helps readers resume a book without spoilers.

The core idea is simple:

- upload an EPUB
- read inside a browser-based reader
- save reading position automatically
- tap for a recap that only uses text the reader has already passed

The recap system is intentionally spoiler-fenced. The backend only retrieves chunks whose `end_char` is at or before the reader's current position, so generated summaries stay behind the page the user is on.

## Stack

- Frontend: React + Vite
- Backend: Flask
- Database and storage: Supabase
- Authentication: backend-owned session + Google OAuth
- LLM and embeddings: OpenAI

## Repository Layout

```text
pageback/
  frontend/   # React app, auth, library, reader UI
  backend/    # Flask API, ingestion, recap services, tests
  .gitignore
  README.md
```

Additional app-specific documentation lives here:

- [backend/README.md](/Users/saketh/Projects/Pageback/backend/README.md)
- [frontend/README.md](/Users/saketh/Projects/Pageback/frontend/README.md)

## How It Works

1. A user signs in with Google through the backend auth flow.
2. The frontend uploads an EPUB to the backend.
3. The backend stores the original file in Supabase Storage.
4. The user opts-in to AI ingestion (optionally in the background); ingestion parses the EPUB, chunks the text, embeds the chunks, and stores them in Supabase.
5. While reading, the frontend saves the latest CFI and character offset.
6. When the reader asks for a recap, the backend resolves a spoiler-safe text window and sends only that window to the LLM.

## Getting Started

### 1. Prerequisites

- Python 3.11+ recommended
- Node.js 18+ recommended
- npm
- Redis installed locally (`redis-server` on your `PATH`)
- A Supabase project
- A Google OAuth client
- An OpenAI API key or a Gemini API key (depending on `LLM_PROVIDER`)

The helper scripts assume these local binaries already exist:

- `python3` for creating the backend virtualenv
- `npm` for installing frontend dependencies
- `redis-server` for local background ingestion via Celery

On macOS with Homebrew, install Redis with:

```bash
brew install redis
```

## Supabase Schema Source Of Truth

The repository now tracks database structure in [`supabase/migrations/`](/Users/saketh/Projects/Pageback/supabase/migrations).

- The checked-in migrations are the intended source of truth for tables, indexes, RPCs, and required storage bucket setup.
- The current migrations include a baseline captured from the existing hosted Supabase project plus a follow-up alignment migration for app/code mismatches.
- The generated Supabase CLI config lives in [`supabase/config.toml`](/Users/saketh/Projects/Pageback/supabase/config.toml).
- See [`supabase/README.md`](/Users/saketh/Projects/Pageback/supabase/README.md) for notes on what was aligned and why.

### 2. Configure Supabase

You need a Supabase project with:

- a storage bucket named `books`
- the SQL schema and RPC function described in the project spec
- an application users table for backend-owned identities

If you have not created the schema yet, set up the tables and the `match_chunks` RPC in the Supabase SQL editor before trying the full flow.

### 3. Run Local Setup

```bash
./scripts/setup_local.sh
```

Use `./scripts/setup_local.sh --all` if you want the script to prompt for optional environment values instead of silently using the local defaults.

This script will:

- prompt for required backend environment values
- use default values for optional backend and frontend env settings unless `--all` is passed
- create `backend/.env`
- create `frontend/.env`
- create `backend/.venv`
- install backend Python dependencies
- install frontend npm dependencies

Before running it, make sure `python3` and `npm` are installed locally. `setup_local.sh` checks for both and exits early if either is missing.

### 4. Test the Backend

#### Unit tests

```bash
cd backend
source .venv/bin/activate
pytest tests/unit -v
```

These are intended to run without external services, although the current code still expects backend env vars to exist during import.

#### Integration tests

```bash
cd backend
cp .env .env.test
source .venv/bin/activate
pytest tests/integration -v
```

Integration tests require working Supabase and OpenAI credentials in `backend/.env.test`.

#### Coverage

```bash
cd backend
source .venv/bin/activate
pytest --cov=app tests --cov-report=term-missing
```

### 5. Test the Frontend

There is no dedicated frontend test suite in the repo yet. The current verification step is a production build:

```bash
cd frontend
npm run build
```

For interactive testing during development, run the frontend locally and exercise the flows in the browser.

### 6. Start the Backend

```bash
./scripts/start_backend.sh
```

Before starting the backend, make sure Redis is installed locally so the script can launch `redis-server` automatically for background ingestion.

The backend listens on `http://localhost:5050` by default.

Useful backend URLs:

- App API base: `http://localhost:5050/api/v1`
- Auth status: `http://localhost:5050/api/v1/auth/me`

### 7. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend runs on `http://localhost:5173`.

### 8. Access the App

- Open `http://localhost:5173` in your browser for the UI.
- The frontend talks to the backend at `http://localhost:5050` through `VITE_API_BASE_URL`.
- Sign in with Google, upload a small EPUB, wait for ingestion to complete, then open the reader view.

### 9. Manual Setup Fallback

If you prefer not to use the helper script, the equivalent manual commands are:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

```bash
cd frontend
npm install
cp .env.example .env
```

Fill in `backend/.env` and `frontend/.env`, then use the test and start commands above.

For Google OAuth local development, make sure your Google client is configured with the local backend callback URL:

- `http://localhost:5050/api/v1/auth/google/callback`

and the frontend origin:

- `http://localhost:5173`

## Environment Variables

### Backend

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for recap generation and embeddings |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Used by the backend for DB and storage operations |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `BACKEND_PORT` | No | Defaults to `5050` for local development |
| `GOOGLE_REDIRECT_URI` | No | Defaults to `http://localhost:5050/api/v1/auth/google/callback` |
| `LLM_PROVIDER` | No | Defaults to `openai` |
| `FLASK_SECRET_KEY` | Yes | Flask app secret |
| `FLASK_ENV` | No | Use `development` locally |
| `FRONTEND_URL` | No | Frontend origin for redirects and CORS |
| `SESSION_COOKIE_NAME` | No | Defaults to `pageback_session` |
| `SESSION_COOKIE_SAMESITE` | No | Defaults to `Lax` |
| `SESSION_COOKIE_SECURE` | No | Use `true` behind HTTPS |

### Frontend

| Variable | Required | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | Yes | Flask API base URL |
| `VITE_ENV` | No | Use `development` locally |

## Development Workflow

### Typical local flow

1. Start the backend (`./scripts/start_backend.sh`) (it starts Redis + Celery automatically).
3. Start the frontend.
4. Open `http://localhost:5173`.
5. Sign in with Google.
6. Upload a small EPUB.
7. Open the book and move a few pages (basic reading works immediately).
8. Enable AI processing (background recommended).
9. Trigger recap levels once AI processing finishes.

### Manual end-to-end checklist

1. Login page renders correctly.
2. Upload creates a book as `ready` and the reader opens immediately.
3. Enable AI processing (background); observe progress + errors in the reader UI.
4. The book moves to `processing` and then `complete` after ingestion finishes.
5. `book_chunks` rows appear in Supabase with embeddings.
6. The reader restores saved position.
7. Recaps return cached responses on repeated requests.

## Current Limitations

- EPUB is implemented; PDF is scaffolded but not supported yet.
- Background ingestion uses Celery/Redis for production-like behavior.
- Recap cache is in-memory only.
- Claude provider is stubbed; Gemini provider is implemented.

## Notes for Future Work

- replace ad-hoc threads with Celery + Redis
- move recap cache to Redis
- add PDF parsing and reading support
- support streamed recap responses
- add malware scanning on upload
