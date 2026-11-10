from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # --- Database ---
    # For local dev: postgresql+psycopg://user:pass@localhost:5432/disha
    # For Neon: postgresql+psycopg://user:pass@ep-xxx.neon.tech/disha?sslmode=require
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/disha"
    # Set true on Vercel/Neon so SQLAlchemy does not keep a connection pool
    # (Neon's pooler handles pooling; SQLAlchemy's pool would exhaust the limit).
    use_null_pool: bool = False

    @field_validator("database_url")
    @classmethod
    def _use_psycopg(cls, url: str) -> str:
        """Accept the plain URL Neon shows (postgres:// or postgresql://) and use psycopg 3."""
        url = url.strip()
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url

    # --- Auth ---
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 720

    # --- CORS ---
    # Comma-separated list of allowed origins.
    # On Vercel, add your frontend URL, e.g. https://my-app.vercel.app
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    # --- Startup behaviour ---
    auto_migrate: bool = True
    auto_seed: bool = True
    # Seed the 60-student demo cohort (false = only admin + reference data)
    seed_demo_data: bool = True

    # --- Default admin account (created if the DB is empty) ---
    default_admin_email: str = "admin@disha.demo"
    default_admin_password: str = "disha123"
    default_admin_name: str = "Suresh Pillai"

    # --- Demo accounts shown on the sign-in page ---
    demo_password: str = "disha123"
    show_demo_accounts: bool = True

    # --- Passwords ---
    # false = stored as plain text (team's current choice for the demo).
    # true  = PBKDF2-SHA256 hashes; existing plain passwords keep working
    #         and are upgraded the next time each user signs in.
    hash_passwords: bool = False

    # --- Chatbot (optional Ollama) ---
    # Leave OLLAMA_MODEL empty to use the built-in rule-based replies.
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
