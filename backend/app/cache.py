"""Fast repeat reads: ETags from a change counter, plus an in-process response cache.

The ETag is a short hash of (what is being read, data_version, 5-minute window).
- The browser sends it back in If-None-Match; when nothing was committed since,
  the answer is 304 Not Modified with no body (two small queries in total: the
  signed-in user, and the version).
- When the browser has no copy but this process built the same response a moment
  ago, the stored bytes are sent without querying the tables again.
The 5-minute window refreshes responses that depend on the clock (upcoming
meetings, "this week") even when no data changed.
"""
import hashlib
import json
import time
from collections import OrderedDict
from typing import Callable

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session

WINDOW_SECONDS = 300
MAX_ENTRIES = 256
_store: "OrderedDict[str, tuple[str, bytes]]" = OrderedDict()


def data_version(db: Session) -> int:
    v = db.info.get("data_version")
    if v is None:
        v = db.info["data_version"] = db.scalar(text("SELECT version FROM data_version WHERE id = 1")) or 0
    return v


def etag_for(key: str, version: int) -> str:
    raw = f"{key}|{version}|{int(time.time() // WINDOW_SECONDS)}".encode()
    return '"' + hashlib.blake2b(raw, digest_size=10).hexdigest() + '"'


def cached_json(request: Request, db: Session, key: str, build: Callable[[], object]) -> Response:
    """Answer a GET with 304, a stored body, or a freshly built one, all with an ETag."""
    tag = etag_for(key, data_version(db))
    headers = {"ETag": tag, "Cache-Control": "private, no-cache", "Vary": "Authorization"}
    if tag in request.headers.get("if-none-match", ""):
        return Response(status_code=304, headers=headers)
    hit = _store.get(key)
    if hit is not None and hit[0] == tag:
        _store.move_to_end(key)
        body = hit[1]
    else:
        body = json.dumps(jsonable_encoder(build()), separators=(",", ":"), ensure_ascii=False).encode()
        _store[key] = (tag, body)
        _store.move_to_end(key)
        while len(_store) > MAX_ENTRIES:
            _store.popitem(last=False)
    return Response(body, media_type="application/json", headers=headers)
