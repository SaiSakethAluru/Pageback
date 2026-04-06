import os

from dotenv import load_dotenv


load_dotenv()


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
