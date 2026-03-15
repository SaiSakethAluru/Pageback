import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:5000/api/v1/auth/google/callback",
    )
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
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

    @classmethod
    def validate(cls) -> None:
        required = {
            "OPENAI_API_KEY": cls.OPENAI_API_KEY,
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_SERVICE_KEY": cls.SUPABASE_SERVICE_KEY,
            "GOOGLE_CLIENT_ID": cls.GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": cls.GOOGLE_CLIENT_SECRET,
            "FLASK_SECRET_KEY": cls.FLASK_SECRET_KEY,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise EnvironmentError(
                f"Missing required environment variables: {joined}. "
                "Set them in backend/.env before starting the app."
            )
