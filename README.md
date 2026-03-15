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
4. A background ingestion job parses the EPUB, chunks the text, embeds the chunks, and stores them in Supabase.
5. While reading, the frontend saves the latest CFI and character offset.
6. When the reader asks for a recap, the backend resolves a spoiler-safe text window and sends only that window to the LLM.

## Getting Started

### 1. Prerequisites

- Python 3.11+ recommended
- Node.js 18+ recommended
- npm
- A Supabase project
- A Google OAuth client
- An OpenAI API key

### 2. Configure Supabase

You need a Supabase project with:

- a storage bucket named `books`
- the SQL schema and RPC function described in the project spec
- an application users table for backend-owned identities

If you have not created the schema yet, set up the tables and the `match_chunks` RPC in the Supabase SQL editor before trying the full flow.

### 3. Start the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `backend/.env`, then run:

```bash
python run.py
```

The backend listens on `http://localhost:5000`.

### 4. Start the Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Fill in `frontend/.env`, then run:

```bash
npm run dev
```

The frontend runs on `http://localhost:5173`.

## Environment Variables

### Backend

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for recap generation and embeddings |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Used by the backend for DB and storage operations |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | No | Defaults to `http://localhost:5000/api/v1/auth/google/callback` |
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

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:5173`.
4. Sign in with Google.
5. Upload a small EPUB.
6. Wait for ingestion to finish.
7. Open the book and move a few pages.
8. Trigger recap levels from the floating action button.

### Manual end-to-end checklist

1. Login page renders correctly.
2. Upload begins and status polling works.
3. The book moves from `pending` to `processing` to `complete`.
4. `book_chunks` rows appear in Supabase with embeddings.
5. The reader restores saved position.
6. Recaps return cached responses on repeated requests.

## Testing

### Unit tests

```bash
cd backend
source venv/bin/activate
pytest tests/unit/ -v
```

These are intended to run without external services.

### Integration tests

```bash
cd backend
cp .env .env.test
source venv/bin/activate
pytest tests/integration/ -v
```

Integration tests require working Supabase and OpenAI credentials in `.env.test`.

### Coverage

```bash
cd backend
source venv/bin/activate
pytest --cov=app tests/ --cov-report=term-missing
```

## Current Limitations

- EPUB is implemented; PDF is scaffolded but not supported yet.
- Background ingestion currently uses `threading.Thread`, which is acceptable for local development but not for production scale.
- Recap cache is in-memory only.
- Claude and Gemini providers are stubbed.

## Notes for Future Work

- replace ad-hoc threads with Celery + Redis
- move recap cache to Redis
- add PDF parsing and reading support
- support streamed recap responses
- add malware scanning on upload
