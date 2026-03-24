#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_ENV_FILE="$BACKEND_DIR/.env"
FRONTEND_ENV_FILE="$FRONTEND_DIR/.env"
BACKEND_VENV_DIR="$BACKEND_DIR/.venv"
BACKEND_PIP="$BACKEND_VENV_DIR/bin/pip"
PROMPT_ALL_OPTIONAL=false

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
      printf '\n' >&2
    else
      read -r -p "$label$prompt_suffix: " value
    fi

    if [[ -z "$value" && -n "$default_value" ]]; then
      value="$default_value"
    fi

    # Normalize clipboard pastes that may include a trailing carriage return.
    value="${value%$'\r'}"

    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return 0
    fi

    printf 'A value is required for %s.\n' "$label" >&2
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
  value="${value%$'\r'}"
  printf '%s' "$value"
}

resolve_optional_value() {
  local label="$1"
  local default_value="${2:-}"

  if [[ "$PROMPT_ALL_OPTIONAL" == "true" ]]; then
    prompt_optional_value "$label" "$default_value"
    return 0
  fi

  printf '%s' "$default_value"
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

print_usage() {
  printf 'Usage: %s [--all]\n' "$(basename "$0")"
  printf '\n'
  printf 'Options:\n'
  printf '  --all   Prompt for optional environment values instead of silently using defaults.\n'
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --all)
        PROMPT_ALL_OPTIONAL=true
        ;;
      -h|--help)
        print_usage
        exit 0
        ;;
      *)
        printf 'Unknown option: %s\n' "$1" >&2
        print_usage >&2
        exit 1
        ;;
    esac
    shift
  done
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

parse_args "$@"
ensure_command python3
ensure_command npm

printf 'This script will create local env files for the backend and frontend.\n'
printf 'Secrets stay on your machine in backend/.env and are already gitignored.\n\n'

llm_provider="$(prompt_optional_value "LLM provider" "openai")"

openai_api_key=""
gemini_api_key=""
gemini_recap_model="gemini-1.5-flash"
gemini_embedding_model="embedding-001"

if [[ "$llm_provider" == "openai" ]]; then
  openai_api_key="$(prompt_value "OpenAI API key" "" true)"
fi

if [[ "$llm_provider" == "gemini" ]]; then
  gemini_api_key="$(prompt_value "Gemini API key" "" true)"
  gemini_recap_model="$(prompt_optional_value "Gemini recap model" "gemini-1.5-flash")"
  gemini_embedding_model="$(prompt_optional_value "Gemini embedding model" "embedding-001")"
fi

redis_url="$(resolve_optional_value "Redis URL" "redis://localhost:6379/0")"

supabase_url="$(prompt_value "Supabase URL" "https://your-project.supabase.co")"
supabase_service_key="$(prompt_value "Supabase service key" "" true)"
google_client_id="$(prompt_value "Google client ID" "" true)"
google_client_secret="$(prompt_value "Google client secret" "" true)"

generated_flask_secret="$(generate_flask_secret)"
flask_secret_key="$(resolve_optional_value "Flask secret key" "$generated_flask_secret")"

frontend_url="$(resolve_optional_value "Frontend URL" "http://localhost:5173")"
backend_port="$(resolve_optional_value "Backend port" "5050")"
google_redirect_uri="$(resolve_optional_value "Google redirect URI" "http://localhost:${backend_port}/api/v1/auth/google/callback")"
flask_env="$(resolve_optional_value "Flask environment" "development")"
session_cookie_name="$(resolve_optional_value "Session cookie name" "pageback_session")"
session_cookie_samesite="$(resolve_optional_value "Session cookie SameSite" "Lax")"
session_cookie_secure="$(resolve_optional_value "Session cookie secure" "false")"
vite_api_base_url="$(resolve_optional_value "Frontend API base URL" "http://localhost:${backend_port}")"
vite_env="$(resolve_optional_value "Frontend environment" "development")"

mkdir -p "$BACKEND_DIR" "$FRONTEND_DIR"

printf 'Writing %s\n' "$BACKEND_ENV_FILE"
cat > "$BACKEND_ENV_FILE" <<EOF
BACKEND_PORT=$backend_port
OPENAI_API_KEY=$openai_api_key
GEMINI_API_KEY=$gemini_api_key
GEMINI_RECAP_MODEL=$gemini_recap_model
GEMINI_EMBEDDING_MODEL=$gemini_embedding_model
REDIS_URL=$redis_url
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
