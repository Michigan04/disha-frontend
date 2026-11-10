"""Ask Disha. Passes the question to a local model through Ollama, which is told to
reply in the JSON schema the frontend sends. When no model is configured, or the
administrator has switched the language model off, this answers 503 and the app
falls back to its built-in rule-based replies."""
import json

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas
from ..config import get_settings
from ..database import get_db
from ..deps import current_user
from ..services import records

router = APIRouter(prefix="/api", tags=["Chat"])


@router.get("/chat/status", summary="Whether a live language model will answer")
def status(_: m.User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_settings()
    return {"live": bool(s.ollama_model) and bool(records.get_setting(db, "llm_enabled", True)), "model": s.ollama_model or None}


@router.post("/chat", summary="Ask the assistant a question")
def chat(body: schemas.ChatIn, _: m.User = Depends(current_user), db: Session = Depends(get_db)):
    s = get_settings()
    if not s.ollama_model:
        raise HTTPException(503, "No language model is configured (set OLLAMA_MODEL).")
    if not records.get_setting(db, "llm_enabled", True):
        raise HTTPException(503, "The language model is switched off by the administrator.")
    messages = [{"role": "system", "content": body.system + "\n\nStudent context:\n" + json.dumps(body.context)}, *body.messages[-12:]]
    payload = {"model": s.ollama_model, "messages": messages, "stream": False, "options": {"temperature": 0.2}}
    if body.response_schema:
        payload["format"] = body.response_schema
    try:
        r = httpx.post(f"{s.ollama_url}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        return {"response": json.loads(r.json()["message"]["content"])}
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(502, "The language model did not give a usable reply.")
