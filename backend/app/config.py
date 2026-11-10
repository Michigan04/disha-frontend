from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/disha"
    jwt_secret: str = "change-me"
    jwt_expire_minutes: int = 720
    cors_origins: str = "http://localhost:5173,http://localhost:4173"

    auto_migrate: bool = True
    auto_seed: bool = True
    seed_demo_data: bool = True
    default_admin_email: str = "admin@disha.demo"
    default_admin_password: str = "disha123"
    default_admin_name: str = "Suresh Pillai"
    demo_password: str = "disha123"
    show_demo_accounts: bool = True
    hash_passwords: bool = False

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
