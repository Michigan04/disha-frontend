"""Disha API. Run from the backend folder:  uvicorn app.main:app --reload

Swagger UI is at /docs, ReDoc at /redoc, the OpenAPI document at /openapi.json.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .bootstrap import initialize
from .config import get_settings
from .database import engine
from .routers import admin, auth, chat, staff, student


@asynccontextmanager
async def lifespan(_: FastAPI):
    # On Vercel (VERCEL=1) api/index.py does this once per cold start and catches
    # errors; a failing lifespan would take the whole function down.
    if not os.environ.get("VERCEL"):
        initialize()
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
    allow_methods=["*"], allow_headers=["*"], expose_headers=["ETag"],
)
# JSON compresses about 6:1; the staff dashboard drops from ~100 KB to ~15 KB.
app.add_middleware(GZipMiddleware, minimum_size=1024)
for r in (auth, student, staff, admin, chat):
    app.include_router(r.router)


@app.get("/api/health", tags=["System"], summary="Is the API up and can it reach the database?")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("select 1"))
    except Exception as exc:  # report it instead of crashing the (serverless) process
        return JSONResponse({"status": "error", "database": "unreachable", "error": type(exc).__name__,
                             "host": engine.url.host}, status_code=503)
    return {"status": "ok", "database": engine.url.host}
