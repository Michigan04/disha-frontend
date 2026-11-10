from urllib.parse import urlparse

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from .config import get_settings


def _make_engine():
    settings = get_settings()
    url = settings.database_url
    connect_args = {
        "connect_timeout": 10,
        # Detect a dead connection quickly (a serverless instance can be frozen
        # for minutes), instead of hanging until the function times out.
        "keepalives": 1, "keepalives_idle": 30, "keepalives_interval": 10, "keepalives_count": 3,
        "tcp_user_timeout": 10_000,
    }
    # A transaction-mode pooler (Neon's "-pooler" host, PgBouncer) does not keep
    # server-side prepared statements between transactions, so do not create any.
    if "-pooler" in (urlparse(url.replace("+psycopg", "")).hostname or "") or settings.use_null_pool:
        connect_args["prepare_threshold"] = None
    if settings.use_null_pool:
        return create_engine(url, poolclass=NullPool, connect_args=connect_args)
    # A small pool: a warm serverless instance reuses its connection and skips the
    # TLS and authentication handshake. Recycled after a minute so a connection
    # left over from a frozen instance is replaced rather than pinged.
    return create_engine(url, pool_pre_ping=True, pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow,
                         pool_recycle=60 if settings.db_pool_size <= 2 else 1800, connect_args=connect_args)


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


# ---------- Change counter ----------
# Every commit that wrote something bumps data_version.version. GET responses put
# it in their ETag (see cache.py), so the browser can ask "has anything changed?"
# and get 304 Not Modified, at the cost of one tiny query.

@event.listens_for(Session, "after_flush")
def _flushed(session, _ctx):
    session.info["changed"] = True


@event.listens_for(Session, "do_orm_execute")
def _bulk_dml(state):
    if state.is_insert or state.is_update or state.is_delete:
        state.session.info["changed"] = True


@event.listens_for(Session, "before_commit")
def _bump_version(session):
    session.flush()
    if session.info.pop("changed", False):
        session.execute(text("INSERT INTO data_version (id, version) VALUES (1, 1) "
                             "ON CONFLICT (id) DO UPDATE SET version = data_version.version + 1"))
    session.info.pop("data_version", None)


@event.listens_for(Session, "after_rollback")
def _rolled_back(session):
    session.info.pop("changed", None)
