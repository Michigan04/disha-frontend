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
import logging
import sys
from pathlib import Path

# The backend package lives in ../backend (bundled through vercel.json "includeFiles").
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.bootstrap import initialize  # noqa: E402
from app.main import app  # noqa: E402,F401  (the ASGI app Vercel serves)

# Runs only when AUTO_MIGRATE / AUTO_SEED are true. The runtime may not send
# ASGI lifespan events, so do it here; both steps are safe to repeat.
try:
    initialize()
except Exception:  # keep serving; /api/health will show the database problem
    logging.getLogger("disha").exception("Database initialisation failed")
