import os
import json
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

_CONFIG_DIR = Path(__file__).resolve().parent / "app_config"


def _load_json_config(filename: str) -> dict:
    filepath = _CONFIG_DIR / filename
    try:
        with filepath.open(encoding="utf-8") as config_file:
            data = json.load(config_file)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value else default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value else default


def _gemini_embedding_model() -> str:
    configured = os.getenv("GEMINI_EMBEDDING_MODEL")
    if configured == "embedding-001":
        return "gemini-embedding-001"
    return configured or "gemini-embedding-001"


class Config:
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "5050"))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        f"http://localhost:{BACKEND_PORT}/api/v1/auth/google/callback",
    )
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_RECAP_MODEL = os.getenv("GEMINI_RECAP_MODEL", "gemini-1.5-flash")
    GEMINI_EMBEDDING_MODEL = _gemini_embedding_model()

    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "pageback_session")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    MAX_UPLOAD_SIZE_MB = 50
    RECAP_TOKEN_BUDGETS = [150, 400, 1200, 4000, 8000]
    RECAP_OUTPUT_INSTRUCTIONS = [
        "1 sentence",
        "2-3 sentences",
        "1 paragraph",
        "2 paragraphs",
        "structured summary with key events and character status",
    ]
    CHUNK_SIZE_TOKENS = 500
    CHUNK_OVERLAP_TOKENS = 50

    # Celery / Redis for background ingestion.
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    CELERY_WORKER_CONCURRENCY = _int_env("CELERY_WORKER_CONCURRENCY", 1)
    INGESTION_LOG_DIR = os.getenv(
        "INGESTION_LOG_DIR",
        str(Path(__file__).resolve().parent.parent / ".logs" / "ingestion"),
    )
    LLM_LIMITS = _load_json_config("llm_limits.json")
    _GEMINI_EMBEDDING_LIMITS = LLM_LIMITS.get("gemini", {}).get("embedding", {})
    _GEMINI_EMBEDDING_RETRY = _GEMINI_EMBEDDING_LIMITS.get("retry", {})
    GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY = _int_env(
        "GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY",
        int(_GEMINI_EMBEDDING_LIMITS.get("output_dimensionality", 1536)),
    )
    GEMINI_EMBEDDING_REQUESTS_PER_MINUTE = _int_env(
        "GEMINI_EMBEDDING_REQUESTS_PER_MINUTE",
        int(_GEMINI_EMBEDDING_LIMITS.get("requests_per_minute", 100)),
    )
    GEMINI_EMBEDDING_INPUT_TOKENS_PER_MINUTE = _int_env(
        "GEMINI_EMBEDDING_INPUT_TOKENS_PER_MINUTE",
        int(_GEMINI_EMBEDDING_LIMITS.get("input_tokens_per_minute", 30000)),
    )
    GEMINI_EMBEDDING_REQUESTS_PER_DAY = _int_env(
        "GEMINI_EMBEDDING_REQUESTS_PER_DAY",
        int(_GEMINI_EMBEDDING_LIMITS.get("requests_per_day", 1000)),
    )
    GEMINI_EMBEDDING_MAX_BATCH_CHUNKS = _int_env(
        "GEMINI_EMBEDDING_MAX_BATCH_CHUNKS",
        int(_GEMINI_EMBEDDING_LIMITS.get("max_batch_chunks", 100)),
    )
    GEMINI_EMBEDDING_MAX_BATCH_INPUT_TOKENS = _int_env(
        "GEMINI_EMBEDDING_MAX_BATCH_INPUT_TOKENS",
        int(_GEMINI_EMBEDDING_LIMITS.get("max_batch_input_tokens", 25000)),
    )
    GEMINI_EMBEDDING_INTER_BATCH_JITTER_SECONDS = _float_env(
        "GEMINI_EMBEDDING_INTER_BATCH_JITTER_SECONDS",
        float(_GEMINI_EMBEDDING_LIMITS.get("inter_batch_jitter_seconds", 1.5)),
    )
    GEMINI_EMBEDDING_RETRY_MAX_ATTEMPTS = _int_env(
        "GEMINI_EMBEDDING_RETRY_MAX_ATTEMPTS",
        int(_GEMINI_EMBEDDING_RETRY.get("max_attempts", 5)),
    )
    GEMINI_EMBEDDING_RETRY_INITIAL_DELAY_SECONDS = _float_env(
        "GEMINI_EMBEDDING_RETRY_INITIAL_DELAY_SECONDS",
        float(_GEMINI_EMBEDDING_RETRY.get("initial_delay_seconds", 2)),
    )
    GEMINI_EMBEDDING_RETRY_MAX_DELAY_SECONDS = _float_env(
        "GEMINI_EMBEDDING_RETRY_MAX_DELAY_SECONDS",
        float(_GEMINI_EMBEDDING_RETRY.get("max_delay_seconds", 60)),
    )
    GEMINI_EMBEDDING_RETRY_JITTER_SECONDS = _float_env(
        "GEMINI_EMBEDDING_RETRY_JITTER_SECONDS",
        float(_GEMINI_EMBEDDING_RETRY.get("jitter_seconds", 1)),
    )

    @classmethod
    def validate(cls) -> None:
        required = {
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_SERVICE_KEY": cls.SUPABASE_SERVICE_KEY,
            "GOOGLE_CLIENT_ID": cls.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": cls.GOOGLE_CLIENT_SECRET,
            "FLASK_SECRET_KEY": cls.FLASK_SECRET_KEY,
        }
        provider_required: dict[str, str | None] = {}
        if cls.LLM_PROVIDER == "openai":
            provider_required = {"OPENAI_API_KEY": cls.OPENAI_API_KEY}
        elif cls.LLM_PROVIDER == "gemini":
            provider_required = {"GEMINI_API_KEY": cls.GEMINI_API_KEY}
        elif cls.LLM_PROVIDER == "claude":
            # Placeholder: current code still requires OpenAI env vars for local recap tests.
            # Extend later once Claude integration is implemented.
            provider_required = {"OPENAI_API_KEY": cls.OPENAI_API_KEY}
        else:
            provider_required = {"OPENAI_API_KEY": cls.OPENAI_API_KEY}

        required.update(provider_required)
        missing = [name for name, value in required.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise EnvironmentError(
                f"Missing required environment variables: {joined}. "
                "Set them in backend/.env before starting the app."
            )
