# PageBack

PageBack is an AI-assisted ebook reader built with a React + Vite frontend, a Flask backend, Supabase for auth/storage/database, and OpenAI for recap and embedding workflows.

## Repository Layout

```text
pageback/
  frontend/
  backend/
  .gitignore
  README.md
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Backend runs on `http://localhost:5000`.

## Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs on `http://localhost:5173`.

## Environment Variables

### Backend

- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `LLM_PROVIDER`
- `FLASK_SECRET_KEY`

### Frontend

- `VITE_API_BASE_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_ENV`

## Tests

```bash
cd backend
source venv/bin/activate
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=app tests/ --cov-report=term-missing
```
