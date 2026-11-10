"""Passwords and access tokens.

Passwords are stored as plain text while HASH_PASSWORDS=false (the team's current
choice). Set HASH_PASSWORDS=true to store PBKDF2 hashes instead; existing plain
passwords keep working and are upgraded the next time each user signs in.
"""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings

_PREFIX = "pbkdf2_sha256$"
_ROUNDS = 310_000


def _pbkdf2(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ROUNDS)
    return _PREFIX + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def store_password(password: str) -> str:
    if not get_settings().hash_passwords:
        return password
    return _pbkdf2(password, os.urandom(16))


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith(_PREFIX):
        salt = base64.b64decode(stored[len(_PREFIX):].split("$")[0])
        return hmac.compare_digest(_pbkdf2(password, salt), stored)
    return hmac.compare_digest(password.encode(), stored.encode())


def needs_upgrade(stored: str) -> bool:
    return get_settings().hash_passwords and not stored.startswith(_PREFIX)


def create_token(user_id: str, role: str) -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes)
    return jwt.encode({"sub": user_id, "role": role, "exp": exp}, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
