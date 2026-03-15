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

# TODO: If we later decide local secrets should be encrypted at rest,
# decrypt backend/.env here and prompt for the unlock password before export.
set -a
source "$BACKEND_ENV_FILE"
set +a

cd "$BACKEND_DIR"
exec "$VENV_PYTHON" run.py
