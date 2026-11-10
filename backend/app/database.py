from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    # Neon (and other serverless PG) works best with NullPool: each request
    # gets a fresh connection through Neon's connection pooler, so SQLAlchemy's
    # own pool would create extra idle connections that exceed the free-tier
    # limit. NullPool disables the pool entirely.
    if settings.use_null_pool:
        # prepare_threshold=None: no server-side prepared statements, which a
        # transaction-mode pooler (Neon's -pooler host, PgBouncer) may not keep.
        return create_engine(url, poolclass=NullPool, connect_args={"prepare_threshold": None})
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
