"""Staff portal: the cohort, assignments, interventions and case outcomes."""
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas
from ..database import get_db
from ..deps import case_staff, require, staff_any
from ..services import academics, records, staffdata
from ..services.staffdata import audit
from .student import risk_assessment_out

router = APIRouter(prefix="/api/staff", tags=["Staff"])
admin = require("admin")


def _uuid(value: str, what: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError):
        raise HTTPException(404, f"{what} not found.")


def _student(db: Session, student_id: str) -> m.Student:
    row = db.get(m.Student, _uuid(student_id, "Student"))
    if row is None:
        raise HTTPException(404, "Student not found.")
    return row


def _staff_user(db: Session, user_id: str, what: str = "Staff member") -> m.User:
    row = db.get(m.User, _uuid(user_id, what))
    if row is None or row.role == m.UserRole.student:
        raise HTTPException(404, f"{what} not found.")
    return row


def _shared(db: Session) -> dict:
    out = defaultdict(list)
    for s in db.scalars(select(m.SharedSuggestion).order_by(m.SharedSuggestion.created_at)).all():
        out[str(s.student_id)].append(s.action_key)
    return dict(out)


def _last_recalc(db: Session):
    value = records.get_setting(db, "last_recalculated_at")
    return datetime.fromisoformat(value) if value else None


@router.get("/bootstrap", summary="Everything the staff portal shows, in one call")
def bootstrap(user: m.User = Depends(staff_any), db: Session = Depends(get_db)):
    """Students with their staff-only details, interventions, rules, imports, jobs and
    (administrators only) the user list and audit log."""
    role = records.ROLE_OUT[user.role]
    ref = records.reference(db)
    rules = records.current_rules(db)
    students = records.load_students(db)
    names = staffdata.user_names(db)
    out = {
        "students": students,
        "meta": records.load_meta(db, students, rules, ref),
        "interventions": staffdata.load_interventions(db),
        "rules": rules,
        "ruleHistory": rule_history(db, names),
        "imports": [staffdata.import_out(r, names) for r in db.scalars(
            select(m.DataImport).where(m.DataImport.status.in_([m.ImportStatus.committed, m.ImportStatus.failed]))
            .order_by(m.DataImport.created_at.desc()).limit(50)).all()],
        "jobs": [staffdata.job_out(j) for j in db.scalars(select(m.SystemJob).order_by(m.SystemJob.run_at.desc()).limit(30)).all()],
        "users": [],
        "audit": [],
        "llmEnabled": bool(records.get_setting(db, "llm_enabled", True)),
        "shared": _shared(db),
        "lastRecalc": _last_recalc(db),
    }
    if role == "admin":
        out["users"] = [staffdata.account_out(u) for u in db.scalars(
            select(m.User).where(m.User.role != m.UserRole.student).order_by(m.User.created_at)).all()]
        out["audit"] = [staffdata.audit_out(a, names) for a in db.scalars(
            select(m.AuditLog).order_by(m.AuditLog.created_at.desc()).limit(1000)).all()]
    return out


def rule_history(db: Session, names: dict) -> list[dict]:
    return [{"version": r.version, "effective": r.effective, "at": r.created_at, "by": names.get(r.created_by, "System"),
             "summary": r.summary, "reason": r.reason}
            for r in db.scalars(select(m.RuleVersion).order_by(m.RuleVersion.version)).all()]


@router.get("/students", summary="Students with their risk level, owner and main reason")
def list_students(
    risk: str | None = Query(None, description="high | low | none"),
    level: str | None = Query(None, description="foundation | diploma"),
    owner: str | None = Query(None, description="Staff user id, or 'none' for unassigned"),
    search: str | None = Query(None, description="Part of a name or roll number"),
    limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    _: m.User = Depends(case_staff), db: Session = Depends(get_db),
):
    ref = records.reference(db)
    rules = records.current_rules(db)
    students = records.load_students(db)
    meta = records.load_meta(db, students, rules, ref)
    rows = []
    for s in students:
        mt = meta[s["id"]]
        rk = academics.risk_with(s, rules, ref)["level"]
        if risk and rk != risk:
            continue
        if level and s["level"] != level:
            continue
        if owner and (mt["owner"] or "none") != owner:
            continue
        if search and search.lower() not in f"{s['name']} {s['rollNo']}".lower():
            continue
        why = academics.reasons(s, mt, rules, ref)
        rows.append({"id": s["id"], "name": s["name"], "rollNo": s["rollNo"], "level": s["level"], "term": len(s["terms"]),
                     "cgpa": academics.cgpa(s, ref), "risk": rk, "owner": mt["owner"], "flaggedOn": mt["flaggedOn"],
                     "mainReason": why[0]["text"] if why else None, "reasons": [r["key"] for r in why]})
    order = {"high": 0, "low": 1, "none": 2}
    rows.sort(key=lambda r: (order[r["risk"]], r["name"]))
    return {"total": len(rows), "items": rows[offset:offset + limit]}


@router.get("/students/{student_id}", summary="One student's full record, staff details, risk assessment and interventions")
def get_student(student_id: str, _: m.User = Depends(case_staff), db: Session = Depends(get_db)):
    row = _student(db, student_id)
    ref = records.reference(db)
    rules = records.current_rules(db)
    students = records.load_students(db, [row.id])
    meta = records.load_meta(db, students, rules, ref)[students[0]["id"]]
    return {"student": students[0], "meta": meta, "reasons": academics.reasons(students[0], meta, rules, ref),
            "assessment": risk_assessment_out(db, row.id), "interventions": staffdata.load_interventions(db, row.id)}


@router.post("/assignments", summary="Assign one or many students to a staff member (administrators)")
def assign(body: schemas.AssignIn, user: m.User = Depends(admin), db: Session = Depends(get_db)):
    owner = _staff_user(db, body.owner)
    done = []
    for sid in body.studentIds:
        s = _student(db, sid)
        before = db.get(m.User, s.assigned_staff_id) if s.assigned_staff_id else None
        for old in db.scalars(select(m.StudentAssignment).where(m.StudentAssignment.student_id == s.id, m.StudentAssignment.is_active)).all():
            old.is_active = False
            old.unassigned_at = m.now_naive()
        db.add(m.StudentAssignment(student_id=s.id, staff_user_id=owner.id, assigned_by=user.id, reason=body.reason.strip()))
        s.assigned_staff_id = owner.id
        moved = f"reassigned from {before.full_name} to" if before else "assigned to"
        audit(db, user, "Assignment", f"{s.full_name} {moved} {owner.full_name}. Reason: {body.reason.strip()}.", s.id,
              before={"owner": str(before.id) if before else None}, after={"owner": str(owner.id)})
        done.append(str(s.id))
    db.commit()
    return {"assigned": done, "owner": str(owner.id)}


@router.post("/interventions", summary="Log an intervention, or the support an instructor offered")
def log_intervention(body: schemas.InterventionIn, user: m.User = Depends(staff_any), db: Session = Depends(get_db)):
    s = _student(db, body.studentId)
    course = db.scalar(select(m.Course).where(m.Course.slug == body.courseId)) if body.courseId else None
    referral = _staff_user(db, body.referralTo, "Referral") if body.referralTo else None
    if body.type == "referral" and referral is None:
        raise HTTPException(422, "Choose who the student is referred to.")
    when = body.at or m.now_tz()
    if when > m.now_tz():
        when = m.now_tz()
    if body.outcome != "resolved" and body.followUp is None:
        raise HTTPException(422, "Choose a follow-up date, or set the outcome to Resolved.")

    status, outcome = staffdata.CASE_IN[body.outcome]
    iv = m.Intervention(
        student_id=s.id, staff_user_id=user.id, intervention_type=staffdata.TYPE_IN[body.type], description=body.notes.strip(),
        status=status, outcome=outcome, follow_up_date=body.followUp.date() if body.followUp else None,
        completed_at=m.now_naive() if status == m.InterventionStatus.completed else None, created_at=when,
    )
    iv.detail = m.InterventionDetail(course_id=course.id if course else None, reason_key=body.reason,
                                     referral_to_user_id=referral.id if referral else None, follow_up_at=body.followUp)
    db.add(iv)
    extra = f", referred to {referral.full_name}" if referral else ""
    audit(db, user, "Intervention", f"{body.type.capitalize()} logged for {s.full_name}{extra}. Outcome: {body.outcome.replace('_', ' ')}.", s.id)
    db.commit()
    slug_of = {course.id: course.slug} if course else {}
    return staffdata.intervention_out(iv, slug_of)


@router.put("/students/{student_id}/outcome", summary="Change where a student's case stands")
def set_outcome(student_id: str, body: schemas.OutcomeIn, user: m.User = Depends(case_staff), db: Session = Depends(get_db)):
    s = _student(db, student_id)
    latest = db.scalar(select(m.Intervention).where(m.Intervention.student_id == s.id).order_by(m.Intervention.created_at.desc()).limit(1))
    if latest is None:
        status, outcome = staffdata.CASE_IN[body.outcome]
        latest = m.Intervention(student_id=s.id, staff_user_id=user.id, intervention_type=m.InterventionType.call,
                                description="Status changed on the board.", status=status, outcome=outcome,
                                completed_at=m.now_naive() if status == m.InterventionStatus.completed else None)
        latest.detail = m.InterventionDetail(reason_key="status")
        db.add(latest)
    else:
        staffdata.set_case(db, latest, body.outcome, user)
    audit(db, user, "Outcome", f"{s.full_name}: case marked \"{body.outcome.replace('_', ' ')}\".", s.id)
    db.commit()
    return {"studentId": str(s.id), "outcome": body.outcome}


@router.post("/students/{student_id}/shared", summary="Mark a suggested action as shared with the student, or undo it")
def toggle_shared(student_id: str, body: schemas.SharedIn, user: m.User = Depends(case_staff), db: Session = Depends(get_db)):
    s = _student(db, student_id)
    row = db.scalar(select(m.SharedSuggestion).where(m.SharedSuggestion.student_id == s.id, m.SharedSuggestion.action_key == body.key))
    if row:
        db.delete(row)
    else:
        db.add(m.SharedSuggestion(student_id=s.id, action_key=body.key[:128], shared_by=user.id))
        audit(db, user, "Suggestion shared", f"{s.full_name}: \"{body.text}\"", s.id)
    db.commit()
    return {"studentId": str(s.id), "key": body.key, "shared": row is None}
