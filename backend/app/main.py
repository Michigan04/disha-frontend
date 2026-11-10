"""Disha API. Run from the backend folder:  uvicorn app.main:app --reload

Swagger UI is at /docs, ReDoc at /redoc, the OpenAPI document at /openapi.json.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .config import BACKEND_DIR, get_settings
from .database import SessionLocal, engine
from .routers import admin, auth, chat, staff, student

log = logging.getLogger("disha")


def migrate() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_migrate:
        migrate()
    if settings.auto_seed:
        from .seed import seed_if_empty

        with SessionLocal() as db:
            if seed_if_empty(db):
                log.warning("Empty database seeded. Sign in as %s", settings.default_admin_email)
    yield


TAGS = [
    {"name": "Auth", "description": "Sign in and the signed-in user. Use **Authorize** with an email and password to try the other endpoints."},
    {"name": "Reference", "description": "Course catalogue, program rules, staff directory and course content."},
    {"name": "Student", "description": "The signed-in student's own record, risk and study plan."},
    {"name": "Meetings", "description": "Upcoming meetings."},
    {"name": "Registrations", "description": "Course registration checks against prerequisites."},
    {"name": "Notifications", "description": "In-app notifications."},
    {"name": "Staff", "description": "At-risk students, assignments, interventions and case outcomes."},
    {"name": "Rules", "description": "Risk and milestone rules, with a preview before applying."},
    {"name": "Imports", "description": "CSV uploads: check, confirm, recalculate."},
    {"name": "Admin", "description": "Users, audit log, settings and system jobs."},
    {"name": "Chat", "description": "Ask Disha."},
    {"name": "System", "description": "Health check."},
]

app = FastAPI(
    title="Disha API",
    version="1.0.0",
    description="Backend for **Disha**, the Student Risk Identification and Intervention Platform (IITM BS, Team 026).",
    openapi_tags=TAGS,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware, allow_origins=get_settings().cors_list, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
for r in (auth, student, staff, admin, chat):
    app.include_router(r.router)


@app.get("/api/health", tags=["System"], summary="Is the API up and can it reach the database?")
def health():
    with engine.connect() as conn:
        conn.execute(text("select 1"))
    return {"status": "ok"}
