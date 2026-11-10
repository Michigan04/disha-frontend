import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models as m
from .database import get_db
from .security import decode_token
from .services.records import ROLE_OUT

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def current_user(token: str | None = Depends(oauth2), db: Session = Depends(get_db)) -> m.User:
    problem = HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in to continue.", {"WWW-Authenticate": "Bearer"})
    if not token:
        raise problem
    try:
        user = db.get(m.User, uuid.UUID(decode_token(token)["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise problem
    if user is None or not user.is_active:
        raise problem
    return user


def require(*roles: str):
    """Allow only the given roles (frontend names: student, support, instructor, admin)."""
    def check(user: m.User = Depends(current_user)) -> m.User:
        if ROLE_OUT[user.role] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot do this.")
        return user
    return check


staff_any = require("support", "instructor", "admin")
case_staff = require("support", "admin")
admin_only = require("admin")
