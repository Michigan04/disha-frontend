"""Administrator pages: rules, data uploads, users, audit log, system settings."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas
from ..database import get_db
from ..deps import admin_only, staff_any
from ..security import store_password
from ..services import imports, records, risk, staffdata
from ..services.staffdata import audit
from .staff import rule_history

router = APIRouter(prefix="/api")
MAX_UPLOAD = 5 * 1024 * 1024


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def run_recalculation(db: Session, detail: str, audit_text: str) -> list[dict]:
    """Recalculate risk for everyone, and record it as a job and an audit entry."""
    changes = risk.recalculate(db)
    moved = _count(len(changes), "student changed", "students changed") + " risk level" if changes else "no risk level changed"
    db.add(m.SystemJob(name="Risk recalculation", detail=f"{detail}: {moved}", status="succeeded"))
    new_high = [c for c in changes if c["to"] == "high"]
    if new_high:
        db.add(m.SystemJob(name="Alert: new High-risk students to staff", status="succeeded",
                           detail=f"{_count(len(new_high), 'student', 'students')}, sent in the app"))
    audit(db, None, "Risk recalculation", f"{audit_text}: {moved}.")
    return changes


# ---------- Rules ----------

@router.get("/rules", tags=["Rules"], summary="The rules in force and their version history")
def get_rules(_: m.User = Depends(staff_any), db: Session = Depends(get_db)):
    return {"rules": records.current_rules(db), "history": rule_history(db, staffdata.user_names(db))}


@router.post("/rules/preview", tags=["Rules"], response_model=schemas.RulesPreviewOut, response_model_by_alias=True,
             summary="Check proposed rules: problems, and which students would change level")
def preview_rules(body: schemas.RulesIn, _: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    return risk.preview(db, body.model_dump(exclude_none=True))


@router.post("/rules", tags=["Rules"], summary="Apply new rules as the next version and recalculate risk")
def apply_rules(body: schemas.RulesApplyIn, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    nxt = body.rules.model_dump(exclude_none=True)
    problems = risk.check_rules(nxt, records.reference(db))
    if problems:
        raise HTTPException(422, {"message": "The rules have problems.", "problems": problems})
    saved = risk.apply_rules(db, nxt, body.reason.strip(), user)
    audit(db, user, "Rule change", f"Rules v{saved['version']} from {saved['effective']}. {saved['summary']} Reason: {body.reason.strip()}.",
          entity_type="rules", entity_id=saved["version"])
    changes = run_recalculation(db, f"Rules v{saved['version']}", f"Rules v{saved['version']}")
    db.commit()
    return {"rules": records.current_rules(db), "changes": changes}


# ---------- Data uploads ----------

@router.get("/imports", tags=["Imports"], summary="Import history, newest first")
def list_imports(_: m.User = Depends(staff_any), db: Session = Depends(get_db)):
    names = staffdata.user_names(db)
    return [staffdata.import_out(r, names) for r in db.scalars(select(m.DataImport).order_by(m.DataImport.created_at.desc()).limit(100)).all()]


@router.get("/imports/template/{category}", tags=["Imports"], response_class=PlainTextResponse, summary="A CSV template for an upload category")
def import_template(category: schemas.ImportCategory, _: m.User = Depends(admin_only)):
    return PlainTextResponse(imports.template(category), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="disha_template_{category}.csv"'})


@router.post("/imports/validate", tags=["Imports"], summary="Upload a CSV and check every row. Nothing is applied yet")
async def validate_import(category: schemas.ImportCategory = Form(...), file: UploadFile = File(...),
                          user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    """Returns accepted rows, and rejected rows with their line number and reason.
    Confirm with `POST /api/imports/{importId}/commit`."""
    name = file.filename or "upload.csv"
    if not name.lower().endswith(".csv"):
        raise HTTPException(422, "Choose a .csv file.")
    raw = await file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "That file is over 5 MB. Split it into smaller files.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "The file is not UTF-8 text. Save it as CSV (UTF-8) and try again.")
    result = imports.validate(db, text, category)
    if "error" in result:
        raise HTTPException(422, result["error"])
    row = m.DataImport(
        uploaded_by=user.id, filename=name[:255], import_type=imports.CATEGORIES[category]["type"], status=m.ImportStatus.validated,
        total_rows=result["total"], successful_rows=len(result["accepted"]), failed_rows=len(result["rejected"]),
        validated_rows={"terms": result["terms"], "rows": [{k: v for k, v in r.items() if k != "course"} for r in result["accepted"]]},
        row_errors=result["rejected"],
    )
    db.add(row)
    db.commit()
    return {"importId": str(row.id), **result}


@router.post("/imports/{import_id}/commit", tags=["Imports"], summary="Apply a checked upload, then recalculate risk")
def commit_import(import_id: uuid.UUID, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    row = db.get(m.DataImport, import_id)
    if row is None:
        raise HTTPException(404, "Import not found.")
    if row.status != m.ImportStatus.validated:
        raise HTTPException(409, "This upload has already been applied or has failed.")
    try:
        imports.commit(db, row)
    except Exception:
        db.rollback()
        row = db.get(m.DataImport, import_id)
        row.status, row.completed_at = m.ImportStatus.failed, m.now_naive()
        db.commit()
        raise HTTPException(500, "The upload could not be applied. Nothing was changed.")
    out = staffdata.import_out(row, {user.id: user.full_name})
    audit(db, user, "Data import", f"{out['category']}, {out['term']}: {out['accepted']} rows accepted, {out['rejected']} rejected ({row.filename}).",
          entity_type="import", entity_id=row.id)
    rules = records.current_rules(db)
    changes = run_recalculation(db, f"Rules v{rules['version']}, from {row.filename}", f"After {row.filename}")
    db.commit()
    return {"import": out, "changes": changes}


# ---------- Users ----------

@router.get("/admin/users", tags=["Admin"], summary="Staff accounts")
def list_users(_: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    return [staffdata.account_out(u) for u in db.scalars(select(m.User).where(m.User.role != m.UserRole.student).order_by(m.User.created_at)).all()]


@router.post("/admin/users", tags=["Admin"], status_code=201, summary="Create a staff account")
def create_user(body: schemas.UserCreate, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.scalar(select(m.User.id).where(func.lower(m.User.email) == email)):
        raise HTTPException(409, "An account with this email already exists.")
    course = db.scalar(select(m.Course).where(m.Course.slug == body.courseId)) if body.courseId else None
    new = m.User(email=email, full_name=body.name.strip(), role=records.ROLE_IN[body.role], password_hash=store_password(body.password))
    new.staff_profile = m.StaffProfile(title=body.title, capacity=body.capacity, course_id=course.id if course else None)
    db.add(new)
    db.flush()
    audit(db, user, "Access", f"{new.full_name}: account created with role {body.role}.", entity_type="user", entity_id=new.id)
    db.commit()
    return staffdata.account_out(new)


@router.patch("/admin/users/{user_id}", tags=["Admin"], summary="Change a staff member's role, or deactivate or reactivate the account")
def update_user(user_id: uuid.UUID, body: schemas.UserPatch, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    target = db.get(m.User, user_id)
    if target is None or target.role == m.UserRole.student:
        raise HTTPException(404, "User not found.")
    if target.id == user.id:
        raise HTTPException(409, "You cannot change your own role or deactivate your own account.")
    if body.role == "student":
        raise HTTPException(422, "A staff account cannot be turned into a student account.")
    if body.role and records.ROLE_IN[body.role] != target.role:
        before = records.ROLE_OUT[target.role]
        target.role = records.ROLE_IN[body.role]
        audit(db, user, "Access", f"{target.full_name}: role changed from {before} to {body.role}.", entity_type="user",
              entity_id=target.id, before={"role": before}, after={"role": body.role})
    if body.active is not None and body.active != target.is_active:
        target.is_active = body.active
        audit(db, user, "Access", f"{target.full_name}: account {'reactivated' if body.active else 'deactivated'}.",
              entity_type="user", entity_id=target.id)
    db.commit()
    return staffdata.account_out(target)


# ---------- Audit, settings, jobs ----------

@router.get("/admin/audit", tags=["Admin"], summary="Audit log, newest first")
def audit_log(
    action: str | None = None, actor: str | None = Query(None, description="User id"),
    student: str | None = Query(None, description="Student id"), search: str | None = None,
    since: datetime | None = None, until: datetime | None = None,
    limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0),
    _: m.User = Depends(admin_only), db: Session = Depends(get_db),
):
    q = select(m.AuditLog)
    if action:
        q = q.where(m.AuditLog.action == action)
    if actor:
        q = q.where(m.AuditLog.actor_user_id == uuid.UUID(actor))
    if student:
        q = q.where(m.AuditLog.entity_type == "student", m.AuditLog.entity_id == student)
    if since:
        q = q.where(m.AuditLog.created_at >= since.replace(tzinfo=None))
    if until:
        q = q.where(m.AuditLog.created_at <= until.replace(tzinfo=None))
    names = staffdata.user_names(db)
    rows = [staffdata.audit_out(a, names) for a in db.scalars(q.order_by(m.AuditLog.created_at.desc())).all()]
    if search:
        rows = [r for r in rows if search.lower() in f"{r['who']} {r['action']} {r['details']}".lower()]
    return {"total": len(rows), "items": rows[offset:offset + limit]}


@router.put("/admin/settings/llm", tags=["Admin"], summary="Switch the language model for student messages on or off")
def set_llm(body: schemas.LlmIn, user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    records.set_setting(db, "llm_enabled", body.enabled, user.id)
    audit(db, user, "Setting", "Language model for student messages switched on." if body.enabled else
          "Language model for student messages switched off: students now see the rule-based reasons.", entity_type="setting", entity_id="llm_enabled")
    db.commit()
    return {"enabled": body.enabled}


@router.get("/admin/jobs", tags=["Admin"], summary="Recent system jobs")
def jobs(_: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    return [staffdata.job_out(j) for j in db.scalars(select(m.SystemJob).order_by(m.SystemJob.run_at.desc()).limit(50)).all()]


@router.post("/admin/recalculate", tags=["Admin"], summary="Recalculate every student's risk now")
def recalculate(user: m.User = Depends(admin_only), db: Session = Depends(get_db)):
    rules = records.current_rules(db)
    changes = run_recalculation(db, f"Rules v{rules['version']}, started by {user.full_name}", f"Started by {user.full_name}")
    db.commit()
    return {"changes": changes}
