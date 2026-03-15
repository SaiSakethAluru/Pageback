#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"
FRONTEND_ENV_FILE="$FRONTEND_DIR/.env"
BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
BACKEND_PIP="$BACKEND_VENV_DIR/bin/pip"

prompt_value() {
  local label="$1"
  local default_value="${2:-}"
  local secret="${3:-false}"
  local prompt_suffix=""
  local value=""

  if [[ -n "$default_value" ]]; then
    prompt_suffix=" [$default_value]"
  fi

  while true; do
    if [[ "$secret" == "true" ]]; then
      read -r -s -p "$label$prompt_suffix: " value
      printf '\n'
    else
      read -r -p "$label$prompt_suffix: " value
    fi

    if [[ -z "$value" && -n "$default_value" ]]; then
      value="$default_value"
    fi

    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return 0
    fi

    printf 'A value is required for %s.\n' "$label"
  done
}

prompt_optional_value() {
  local label="$1"
  local default_value="${2:-}"
  local prompt_suffix=""
  local value=""

  if [[ -n "$default_value" ]]; then
    prompt_suffix=" [$default_value]"
  fi

  read -r -p "$label$prompt_suffix: " value
  if [[ -z "$value" ]]; then
    value="$default_value"
  fi
  printf '%s' "$value"
}

generate_flask_secret() {
  python3 -c 'import secrets; print(secrets.token_hex(32))'
}

ensure_command() {
  local command_name="$1"
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$command_name" >&2
    exit 1
  fi
}

install_backend_dependencies() {
  printf '\nSetting up backend virtualenv in %s\n' "$BACKEND_VENV_DIR"
  if [[ ! -d "$BACKEND_VENV_DIR" ]]; then
    python3 -m venv "$BACKEND_VENV_DIR"
  fi
  "$BACKEND_PIP" install -r "$BACKEND_DIR/requirements.txt"
}

install_frontend_dependencies() {
  printf '\nInstalling frontend dependencies in %s\n' "$FRONTEND_DIR"
  (
    cd "$FRONTEND_DIR"
    npm install
  )
}

ensure_command python3
ensure_command npm

printf 'This script will create local env files for the backend and frontend.\n'
printf 'Secrets stay on your machine in backend/.env and are already gitignored.\n\n'

openai_api_key="$(prompt_value "OpenAI API key" "" true)"
supabase_url="$(prompt_value "Supabase URL" "https://your-project.supabase.co")"
supabase_service_key="$(prompt_value "Supabase service key" "" true)"
google_client_id="$(prompt_value "Google client ID" "" true)"
google_client_secret="$(prompt_value "Google client secret" "" true)"

generated_flask_secret="$(generate_flask_secret)"
flask_secret_key="$(prompt_optional_value "Flask secret key" "$generated_flask_secret")"

frontend_url="$(prompt_optional_value "Frontend URL" "http://localhost:5173")"
google_redirect_uri="$(prompt_optional_value "Google redirect URI" "http://localhost:5000/api/v1/auth/google/callback")"
llm_provider="$(prompt_optional_value "LLM provider" "openai")"
flask_env="$(prompt_optional_value "Flask environment" "development")"
session_cookie_name="$(prompt_optional_value "Session cookie name" "pageback_session")"
session_cookie_samesite="$(prompt_optional_value "Session cookie SameSite" "Lax")"
session_cookie_secure="$(prompt_optional_value "Session cookie secure" "false")"
vite_api_base_url="$(prompt_optional_value "Frontend API base URL" "http://localhost:5000")"
vite_env="$(prompt_optional_value "Frontend environment" "development")"

mkdir -p "$BACKEND_DIR" "$FRONTEND_DIR"

printf 'Writing %s\n' "$BACKEND_ENV_FILE"
cat > "$BACKEND_ENV_FILE" <<EOF
OPENAI_API_KEY=$openai_api_key
SUPABASE_URL=$supabase_url
SUPABASE_SERVICE_KEY=$supabase_service_key
GOOGLE_CLIENT_ID=$google_client_id
GOOGLE_CLIENT_SECRET=$google_client_secret
GOOGLE_REDIRECT_URI=$google_redirect_uri
LLM_PROVIDER=$llm_provider
FLASK_SECRET_KEY=$flask_secret_key
FLASK_ENV=$flask_env
FRONTEND_URL=$frontend_url
SESSION_COOKIE_NAME=$session_cookie_name
SESSION_COOKIE_SAMESITE=$session_cookie_samesite
SESSION_COOKIE_SECURE=$session_cookie_secure
EOF

printf 'Writing %s\n' "$FRONTEND_ENV_FILE"
cat > "$FRONTEND_ENV_FILE" <<EOF
VITE_API_BASE_URL=$vite_api_base_url
VITE_ENV=$vite_env
EOF

install_backend_dependencies
install_frontend_dependencies

printf '\nLocal setup is complete.\n'
printf 'Next steps:\n'
printf '  1. Run ./scripts/start_backend.sh\n'
printf '  2. In another terminal: cd frontend && npm run dev\n'
printf '  3. Open http://localhost:5173\n'
