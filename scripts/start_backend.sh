#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [[ ! -f "$BACKEND_ENV_FILE" ]]; then
  printf 'Missing %s. Run ./scripts/setup_local.sh first.\n' "$BACKEND_ENV_FILE" >&2
  exit 1
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  printf 'Missing backend virtualenv at %s.\n' "$VENV_PYTHON" >&2
  printf 'Run: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt\n' >&2
  exit 1
fi

cd "$BACKEND_DIR"

# Let python-dotenv load backend/.env from the backend directory.
# Sourcing the file in bash is fragile because secrets may contain shell
# metacharacters like parentheses, ampersands, or spaces.

# Start Redis (local dev) if not already running.
# This keeps local setup to a single command.
START_REDIS="${START_REDIS:-true}"
if [[ "$START_REDIS" == "true" ]]; then
  if pgrep -f "redis-server.*6379" >/dev/null 2>&1 || pgrep -f "redis-server" >/dev/null 2>&1; then
    :
  else
    if command -v redis-server >/dev/null 2>&1; then
      # Use --daemonize so we can keep this script running Flask/Celery.
      # Note: redis-server is expected to be installed locally.
      redis-server --daemonize yes >/dev/null 2>&1 || true

      # Wait until Redis responds (best-effort).
      if command -v redis-cli >/dev/null 2>&1; then
        for _ in {1..20}; do
          if redis-cli ping >/dev/null 2>&1; then
            break
          fi
          sleep 0.25
        done
      else
        sleep 1
      fi
    else
      printf 'redis-server is not installed.\n' >&2
      printf 'Install Redis (macOS/Homebrew): brew install redis\n' >&2
      printf 'Or start Redis manually and re-run this script.\n' >&2
      exit 1
    fi
  fi
fi

# Start Celery worker for background ingestion.
# This keeps local setup to a single command (plus Redis).
START_CELERY_WORKER="${START_CELERY_WORKER:-true}"
if [[ "$START_CELERY_WORKER" == "true" ]]; then
  # Avoid spawning duplicate workers for the same app.
  if ! pgrep -f "celery -A app.celery_app worker" >/dev/null 2>&1; then
    "$ROOT_DIR/scripts/start_celery_worker.sh" >/dev/null 2>&1 &
  fi
fi

exec "$VENV_PYTHON" run.py
