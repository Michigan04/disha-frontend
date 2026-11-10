"""Database set-up: apply Alembic migrations, then seed an empty database.

Run it once against a new database (for example Neon) before the first deploy:

    cd backend
    DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require" python -m app.bootstrap

Both steps are safe to repeat: migrations stop at the latest version, and seeding
does nothing when the database already has users.
"""
import logging

from .config import BACKEND_DIR, get_settings
from .database import SessionLocal

log = logging.getLogger("disha")


def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


def seed() -> bool:
    from .seed import seed_if_empty

    with SessionLocal() as db:
        return seed_if_empty(db)


def initialize(force: bool = False) -> None:
    """Migrate and seed, as AUTO_MIGRATE and AUTO_SEED allow (or both when force=True)."""
    settings = get_settings()
    if force or settings.auto_migrate:
        migrate()
    if (force or settings.auto_seed) and seed():
        log.warning("Empty database seeded. Sign in as %s", settings.default_admin_email)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("Applying migrations...")
    migrate()
    print("Seeding...")
    print("Seeded the demo data." if seed() else "The database already has users; nothing was seeded.")
    print("Done.")
