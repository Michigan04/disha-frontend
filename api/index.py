"""Vercel serverless handler for the Disha FastAPI backend.

Vercel runs this file as a Python 3.12 Function when any request matches
the /api/** route defined in vercel.json.  It simply imports the FastAPI app
and hands the ASGI request to Mangum, which translates between the AWS Lambda /
Vercel Function calling convention and ASGI.

Environment variables required on Vercel:
  DATABASE_URL   – Neon connection string (postgresql+psycopg://...?sslmode=require)
  USE_NULL_POOL  – true   (NullPool is required for Neon serverless)
  JWT_SECRET     – long random string
  CORS_ORIGINS   – your Vercel frontend URL, e.g. https://my-app.vercel.app
  AUTO_MIGRATE   – true (runs alembic upgrade head on first cold start)
  AUTO_SEED      – true (seeds the DB if it is empty)
  SEED_DEMO_DATA – true / false
  HASH_PASSWORDS – false (plain text; change to true for production)
  SHOW_DEMO_ACCOUNTS – true / false

Optional:
  OLLAMA_URL / OLLAMA_MODEL – leave empty to use the built-in rule-based chat
"""

from mangum import Mangum

from app.main import app  # noqa: F401 – imports the FastAPI app and runs lifespan

handler = Mangum(app, lifespan="auto")
