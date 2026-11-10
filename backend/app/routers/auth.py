from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas
from ..config import get_settings
from ..database import get_db
from ..deps import current_user
from ..security import create_token, needs_upgrade, store_password, verify_password
from ..services import records
from ..services.staffdata import audit

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def user_out(db: Session, u: m.User) -> dict:
    role = records.ROLE_OUT[u.role]
    out = {"id": str(u.id), "email": u.email, "name": u.full_name, "role": role,
           "title": u.staff_profile.title if u.staff_profile else None}
    if role == "student":
        sid = db.scalar(select(m.Student.id).where(m.Student.user_id == u.id))
        out["studentId"] = str(sid) if sid else None
    else:
        out["staffId"] = str(u.id)
        if u.staff_profile and u.staff_profile.course_id:
            out["courseId"] = db.scalar(select(m.Course.slug).where(m.Course.id == u.staff_profile.course_id))
    return out


def _sign_in(db: Session, email: str, password: str, request: Request) -> dict:
    user = db.scalar(select(m.User).where(func.lower(m.User.email) == email.strip().lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(401, "That email and password do not match an account.")
    if not user.is_active:
        raise HTTPException(403, "This account has been deactivated. Ask an administrator.")
    if needs_upgrade(user.password_hash):
        user.password_hash = store_password(password)
    audit(db, user, "Sign in", f"{user.full_name} signed in.", entity_type="user", entity_id=user.id,
          ip=request.client.host if request.client else None)
    db.commit()
    return {"access_token": create_token(str(user.id), user.role.value), "token_type": "bearer", "user": user_out(db, user)}


@router.post("/login", response_model=schemas.TokenOut, summary="Sign in with email and password")
def login(body: schemas.LoginIn, request: Request, db: Session = Depends(get_db)):
    return _sign_in(db, body.email, body.password, request)


@router.post("/token", response_model=schemas.TokenOut, summary="Sign in (form version, used by the Authorize button)")
def token(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return _sign_in(db, form.username, form.password, request)


@router.get("/me", response_model=schemas.UserOut, summary="The signed-in user")
def me(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return user_out(db, user)


@router.get("/demo-accounts", response_model=schemas.DemoAccountsOut,
            summary="Seeded demo accounts for the sign-in page (empty unless SHOW_DEMO_ACCOUNTS=true)")
def demo_accounts(db: Session = Depends(get_db)):
    s = get_settings()
    if not s.show_demo_accounts:
        return {"password": None, "accounts": []}
    return {"password": s.demo_password, "accounts": records.get_setting(db, "demo_accounts", [])}
