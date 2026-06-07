from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://autoab:autoab_secret@localhost:5432/autoab_db"
    sync_database_url: str = "postgresql://autoab:autoab_secret@localhost:5432/autoab_db"

    # ── Redis / Celery ────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── LLM ───────────────────────────────────────────────────
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # ── App ───────────────────────────────────────────────────
    app_name: str = "AutoAB"
    debug: bool = True

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
