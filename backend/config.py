import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
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
            "SUPABASE_ANON_KEY": cls.SUPABASE_ANON_KEY,
            "SUPABASE_SERVICE_KEY": cls.SUPABASE_SERVICE_KEY,
            "FLASK_SECRET_KEY": cls.FLASK_SECRET_KEY,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            joined = ", ".join(missing)
            raise EnvironmentError(
                f"Missing required environment variables: {joined}. "
                "Set them in backend/.env before starting the app."
            )
