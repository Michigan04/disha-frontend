"""Vercel serverless entry point for the Disha FastAPI backend.

Vercel's Python runtime serves the ASGI app named `app` in this file for every
request that vercel.json rewrites here (/api/...). The FastAPI routes already
start with /api, so paths arrive unchanged.

Set up the Neon database once before the first deploy (see README, "Deploy on
Vercel"): `python -m app.bootstrap` from the backend folder with DATABASE_URL
pointing at Neon. Keep AUTO_MIGRATE and AUTO_SEED false on Vercel so cold starts
do not run migrations.

Environment variables (Vercel → Settings → Environment Variables):
  DATABASE_URL    Neon pooled connection string (postgresql://...-pooler...?sslmode=require)
  USE_NULL_POOL   true
  JWT_SECRET      long random string
  AUTO_MIGRATE    false
  AUTO_SEED       false
  Optional: SHOW_DEMO_ACCOUNTS, DEMO_PASSWORD, HASH_PASSWORDS, OLLAMA_URL, OLLAMA_MODEL
"""
import json
import logging
import sys
from pathlib import Path

# The backend package lives in ../backend (bundled through vercel.json "includeFiles").
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

log = logging.getLogger("disha")


def _startup_error(reason: str):
    """A minimal ASGI app that says why the backend could not start."""
    body = json.dumps({"status": "error", "detail": "The backend could not start.", "reason": reason}).encode()

    async def error_app(scope, receive, send):
        if scope["type"] != "http":
            return
        await send({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": body})

    return error_app


try:
    from app.bootstrap import initialize
    from app.main import app as _backend
except Exception as exc:  # show why in the response instead of a bare FUNCTION_INVOCATION_FAILED
    log.exception("The backend could not start")
    _backend = _startup_error(f"{type(exc).__name__}: {exc}")
else:
    # Runs only when AUTO_MIGRATE / AUTO_SEED are true. The runtime may not send
    # ASGI lifespan events, so do it here; both steps are safe to repeat.
    try:
        initialize()
    except Exception:  # keep serving; /api/health shows the database problem
        log.exception("Database initialisation failed")

# Vercel finds the function by this top-level `app` assignment: keep it at module level.
app = _backend
