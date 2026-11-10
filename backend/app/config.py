import hashlib
import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
# Vercel sets VERCEL=1 in its functions; serverless defaults below follow it.
ON_VERCEL = bool(os.environ.get("VERCEL"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    # --- Database ---
    # For local dev: postgresql+psycopg://user:pass@localhost:5432/disha
    # For Neon: postgresql+psycopg://user:pass@ep-xxx.neon.tech/disha?sslmode=require
    # Vercel's Neon integration sets POSTGRES_URL; DATABASE_URL wins when both exist.
    database_url: str = Field("postgresql+psycopg://postgres:postgres@localhost:5432/disha",
                              validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"))
    # Connection pool per process. On Vercel a warm instance keeps one connection
    # (plus a few for bursts) to Neon's pooler; USE_NULL_POOL=true opens a fresh
    # connection for every request instead.
    use_null_pool: bool = False
    db_pool_size: int = 1 if ON_VERCEL else 5
    db_max_overflow: int = 4 if ON_VERCEL else 10

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
    # Unset: derived from DATABASE_URL, so it is secret without extra set-up.
    # Set JWT_SECRET to keep sign-ins valid when the database URL changes.
    jwt_secret: str = ""
    jwt_expire_minutes: int = 720

    # --- CORS ---
    # Comma-separated list of allowed origins.
    # On Vercel, add your frontend URL, e.g. https://my-app.vercel.app
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    # --- Startup behaviour ---
    # Off by default on Vercel: set the database up once with `python -m app.bootstrap`.
    auto_migrate: bool = not ON_VERCEL
    auto_seed: bool = not ON_VERCEL
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

    @model_validator(mode="after")
    def _default_jwt_secret(self):
        if not self.jwt_secret:
            self.jwt_secret = hashlib.sha256(("disha-jwt:" + self.database_url).encode()).hexdigest()
        return self

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
