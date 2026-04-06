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
MENU_TOOL="basic"
GUM_BIN=""
FZF_BIN=""
TEMP_UI_DIR=""

cleanup_temp_ui_dir() {
  if [[ -n "$TEMP_UI_DIR" && -d "$TEMP_UI_DIR" ]]; then
    rm -rf "$TEMP_UI_DIR"
  fi
}

trap cleanup_temp_ui_dir EXIT

get_existing_env_value() {
  local env_file="$1"
  local key="$2"
  local line=""

  if [[ ! -f "$env_file" ]]; then
    return 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    if [[ "${line%%=*}" == "$key" ]]; then
      printf '%s' "${line#*=}"
      return 0
    fi
  done < "$env_file"

  return 1
}

mask_value() {
  local value="$1"
  local secret="${2:-false}"
  local length=${#value}

  if [[ "$secret" != "true" ]]; then
    printf '%s' "$value"
    return 0
  fi

  if (( length <= 8 )); then
    printf '%s' "${value:0:2}***"
    return 0
  fi

  printf '%s***%s' "${value:0:4}" "${value: -4}"
}

prompt_yes_no() {
  local label="$1"
  local default_answer="${2:-y}"
  local prompt_suffix="[Y/n]"
  local reply=""
  local normalized_reply=""

  if [[ "$default_answer" != "y" ]]; then
    prompt_suffix="[y/N]"
  fi

  while true; do
    read -r -p "$label $prompt_suffix " reply
    reply="${reply%$'\r'}"
    if [[ -z "$reply" ]]; then
      reply="$default_answer"
    fi

    normalized_reply="$(printf '%s' "$reply" | tr '[:upper:]' '[:lower:]')"

    case "$normalized_reply" in
      y|yes)
        return 0
        ;;
      n|no)
        return 1
        ;;
    esac

    printf 'Please answer y or n.\n' >&2
  done
}

get_gum_download_url() {
  local os_name
  local arch_name

  os_name="$(uname -s)"
  arch_name="$(uname -m)"

  python3 - "$os_name" "$arch_name" <<'PY'
import json
import sys
import urllib.request

os_name = sys.argv[1]
arch_name = sys.argv[2]

os_map = {
    "Darwin": "Darwin",
    "Linux": "Linux",
}
arch_map = {
    "arm64": "arm64",
    "aarch64": "arm64",
    "x86_64": "x86_64",
    "amd64": "x86_64",
}

target_os = os_map.get(os_name)
target_arch = arch_map.get(arch_name)
if not target_os or not target_arch:
    sys.exit(1)

with urllib.request.urlopen("https://api.github.com/repos/charmbracelet/gum/releases/latest") as response:
    release = json.load(response)

for asset in release.get("assets", []):
    name = asset.get("name", "")
    if target_os in name and target_arch in name and name.endswith(".tar.gz"):
        print(asset["browser_download_url"])
        sys.exit(0)

sys.exit(1)
PY
}

install_temporary_gum() {
  local download_url=""
  local archive_path=""

  if ! command -v curl >/dev/null 2>&1 || ! command -v tar >/dev/null 2>&1; then
    return 1
  fi

  download_url="$(get_gum_download_url)" || return 1
  TEMP_UI_DIR="$(mktemp -d "${TMPDIR:-/tmp}/pageback-gum.XXXXXX")"
  archive_path="$TEMP_UI_DIR/gum.tar.gz"

  curl -fsSL "$download_url" -o "$archive_path" || return 1
  tar -xzf "$archive_path" -C "$TEMP_UI_DIR" || return 1

  if [[ ! -x "$TEMP_UI_DIR/gum" ]]; then
    return 1
  fi

  GUM_BIN="$TEMP_UI_DIR/gum"
  MENU_TOOL="gum"
  return 0
}

setup_menu_tool() {
  if command -v gum >/dev/null 2>&1; then
    GUM_BIN="$(command -v gum)"
    MENU_TOOL="gum"
    printf 'Using gum for interactive prompts.\n\n'
    return 0
  fi

  if command -v fzf >/dev/null 2>&1; then
    FZF_BIN="$(command -v fzf)"
    MENU_TOOL="fzf"
    printf 'Using fzf for interactive choices.\n\n'
    return 0
  fi

  if prompt_yes_no "Install a temporary copy of gum for nicer terminal prompts?" "y"; then
    if install_temporary_gum; then
      printf 'Using a temporary gum binary for interactive prompts.\n\n'
      return 0
    fi
    printf 'Temporary gum install failed. Falling back to the built-in prompts.\n\n' >&2
  fi

  MENU_TOOL="basic"
}

choose_numbered_option() {
  local label="$1"
  shift
  local options=("$@")
  local choice=""
  local index=1
  local entries=()
  local selected=""

  for option in "${options[@]}"; do
    entries+=("${index}) ${option}")
    ((index += 1))
  done

  if [[ "$MENU_TOOL" == "gum" && -n "$GUM_BIN" ]]; then
    selected="$("$GUM_BIN" choose --header "$label" "${entries[@]}")"
    printf '%s' "${selected%%)*}"
    return 0
  fi

  if [[ "$MENU_TOOL" == "fzf" && -n "$FZF_BIN" ]]; then
    selected="$(printf '%s\n' "${entries[@]}" | "$FZF_BIN" --prompt="Select> " --header="$label" --height=10 --border)"
    printf '%s' "${selected%%)*}"
    return 0
  fi

  printf '%s\n' "$label" >&2
  for entry in "${entries[@]}"; do
    printf '  %s\n' "$entry" >&2
  done

  while true; do
    read -r -p "Choose an option [1-${#options[@]}]: " choice
    choice="${choice%$'\r'}"
    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#options[@]} )); then
      printf '%s' "$choice"
      return 0
    fi
    printf 'Please enter a number between 1 and %d.\n' "${#options[@]}" >&2
  done
}

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
  local secret="${3:-false}"
  local prompt_suffix=""
  local value=""

  if [[ -n "$default_value" ]]; then
    prompt_suffix=" [$default_value]"
  fi

  if [[ "$secret" == "true" ]]; then
    read -r -s -p "$label$prompt_suffix: " value
    printf '\n' >&2
  else
    read -r -p "$label$prompt_suffix: " value
  fi

  if [[ -z "$value" ]]; then
    value="$default_value"
  fi
  value="${value%$'\r'}"
  printf '%s' "$value"
}

prompt_value_with_existing() {
  local label="$1"
  local env_file="$2"
  local env_key="$3"
  local default_value="${4:-}"
  local secret="${5:-false}"
  local existing_value=""
  local display_value=""
  local choice=""

  if existing_value="$(get_existing_env_value "$env_file" "$env_key")"; then
    display_value="$(mask_value "$existing_value" "$secret")"
    choice="$(choose_numbered_option "$label" "Reuse existing value ($display_value)" "Enter new value")"
    if [[ "$choice" == "1" ]]; then
      printf '%s' "$existing_value"
      return 0
    fi
  fi

  prompt_value "$label" "$default_value" "$secret"
}

prompt_optional_value_with_existing() {
  local label="$1"
  local env_file="$2"
  local env_key="$3"
  local default_value="${4:-}"
  local secret="${5:-false}"
  local existing_value=""
  local display_value=""
  local choice=""

  if existing_value="$(get_existing_env_value "$env_file" "$env_key")"; then
    display_value="$(mask_value "$existing_value" "$secret")"
    choice="$(choose_numbered_option "$label" "Reuse existing value ($display_value)" "Enter new value")"
    if [[ "$choice" == "1" ]]; then
      printf '%s' "$existing_value"
      return 0
    fi
    prompt_optional_value "$label" "$default_value" "$secret"
    return 0
  fi

  resolve_optional_value "$label" "$default_value"
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
setup_menu_tool

existing_llm_provider="$(get_existing_env_value "$BACKEND_ENV_FILE" "LLM_PROVIDER" || true)"
if [[ -n "$existing_llm_provider" && "$existing_llm_provider" != "openai" && "$existing_llm_provider" != "gemini" ]]; then
  printf 'Existing LLM provider "%s" is unsupported by setup_local.sh.\n' "$existing_llm_provider" >&2
fi

provider_prompt="LLM provider (supported: openai, gemini)"
if [[ -n "$existing_llm_provider" && ( "$existing_llm_provider" == "openai" || "$existing_llm_provider" == "gemini" ) ]]; then
  provider_prompt="$provider_prompt [current: $existing_llm_provider]"
fi
provider_choice="$(choose_numbered_option "$provider_prompt" "openai" "gemini")"
if [[ "$provider_choice" == "1" ]]; then
  llm_provider="openai"
else
  llm_provider="gemini"
fi

openai_api_key=""
gemini_api_key=""
gemini_recap_model="gemini-1.5-flash"
gemini_embedding_model="gemini-embedding-001"

if [[ "$llm_provider" == "openai" ]]; then
  openai_api_key="$(prompt_value_with_existing "OpenAI API key" "$BACKEND_ENV_FILE" "OPENAI_API_KEY" "" true)"
fi

if [[ "$llm_provider" == "gemini" ]]; then
  gemini_api_key="$(prompt_value_with_existing "Gemini API key" "$BACKEND_ENV_FILE" "GEMINI_API_KEY" "" true)"
  gemini_recap_model="$(prompt_optional_value_with_existing "Gemini recap model" "$BACKEND_ENV_FILE" "GEMINI_RECAP_MODEL" "gemini-1.5-flash")"
  gemini_embedding_model="$(prompt_optional_value_with_existing "Gemini embedding model" "$BACKEND_ENV_FILE" "GEMINI_EMBEDDING_MODEL" "gemini-embedding-001")"
fi

redis_url="$(prompt_optional_value_with_existing "Redis URL" "$BACKEND_ENV_FILE" "REDIS_URL" "redis://localhost:6379/0")"

supabase_url="$(prompt_value_with_existing "Supabase URL" "$BACKEND_ENV_FILE" "SUPABASE_URL" "https://your-project.supabase.co")"
supabase_service_key="$(prompt_value_with_existing "Supabase service key" "$BACKEND_ENV_FILE" "SUPABASE_SERVICE_KEY" "" true)"
google_client_id="$(prompt_value_with_existing "Google client ID" "$BACKEND_ENV_FILE" "GOOGLE_CLIENT_ID")"
google_client_secret="$(prompt_value_with_existing "Google client secret" "$BACKEND_ENV_FILE" "GOOGLE_CLIENT_SECRET" "" true)"

generated_flask_secret="$(generate_flask_secret)"
flask_secret_key="$(prompt_optional_value_with_existing "Flask secret key" "$BACKEND_ENV_FILE" "FLASK_SECRET_KEY" "$generated_flask_secret" true)"

frontend_url="$(prompt_optional_value_with_existing "Frontend URL" "$BACKEND_ENV_FILE" "FRONTEND_URL" "http://localhost:5173")"
backend_port="$(prompt_optional_value_with_existing "Backend port" "$BACKEND_ENV_FILE" "BACKEND_PORT" "5050")"
google_redirect_uri="$(prompt_optional_value_with_existing "Google redirect URI" "$BACKEND_ENV_FILE" "GOOGLE_REDIRECT_URI" "http://localhost:${backend_port}/api/v1/auth/google/callback")"
flask_env="$(prompt_optional_value_with_existing "Flask environment" "$BACKEND_ENV_FILE" "FLASK_ENV" "development")"
session_cookie_name="$(prompt_optional_value_with_existing "Session cookie name" "$BACKEND_ENV_FILE" "SESSION_COOKIE_NAME" "pageback_session")"
session_cookie_samesite="$(prompt_optional_value_with_existing "Session cookie SameSite" "$BACKEND_ENV_FILE" "SESSION_COOKIE_SAMESITE" "Lax")"
session_cookie_secure="$(prompt_optional_value_with_existing "Session cookie secure" "$BACKEND_ENV_FILE" "SESSION_COOKIE_SECURE" "false")"
vite_api_base_url="$(prompt_optional_value_with_existing "Frontend API base URL" "$FRONTEND_ENV_FILE" "VITE_API_BASE_URL" "http://localhost:${backend_port}")"
vite_env="$(prompt_optional_value_with_existing "Frontend environment" "$FRONTEND_ENV_FILE" "VITE_ENV" "development")"

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
