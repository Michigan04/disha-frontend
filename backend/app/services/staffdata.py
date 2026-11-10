"""Audit log, interventions, imports and jobs in the shapes the staff pages use."""
from __future__ import annotations

import uuid
from datetime import datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from .records import ROLE_OUT, utc

# ---------- Audit ----------


def audit(db: Session, user: m.User | None, action: str, details: str, student_id=None,
          entity_type: str | None = None, entity_id=None, before=None, after=None, at=None, ip: str | None = None) -> m.AuditLog:
    """Record who did what. `user` None means the system did it."""
    target = entity_id or student_id
    row = m.AuditLog(
        actor_user_id=user.id if user else None, action=action,
        entity_type=entity_type or ("student" if student_id else "system"),
        entity_id=str(target) if target else None,
        before_data=before,
        after_data={"details": details, "student_id": str(student_id) if student_id else None, **(after or {})},
        ip_address=ip, created_at=(at or m.now_tz()).astimezone(timezone.utc).replace(tzinfo=None),
    )
    db.add(row)
    return row


def audit_out(row: m.AuditLog, names: dict) -> dict:
    data = row.after_data or {}
    who = names.get(row.actor_user_id, "System") if row.actor_user_id else "System"
    return {"id": str(row.id), "at": utc(row.created_at), "who": who, "action": row.action,
            "details": data.get("details", ""), "studentId": data.get("student_id")}


# ---------- Interventions ----------
# The pages speak of one "case status"; the DBML splits it into status and outcome.

CASE_IN = {
    "not_contacted": (m.InterventionStatus.open, None),
    "in_progress": (m.InterventionStatus.in_progress, None),
    "no_response": (m.InterventionStatus.in_progress, m.InterventionOutcome.unable_to_contact),
    "escalated": (m.InterventionStatus.in_progress, m.InterventionOutcome.further_support_required),
    "resolved": (m.InterventionStatus.completed, m.InterventionOutcome.improved),
}
TYPE_IN = {"call": m.InterventionType.call, "email": m.InterventionType.email, "meeting": m.InterventionType.meeting,
           "referral": m.InterventionType.academic_counselling}
TYPE_OUT = {m.InterventionType.call: "call", m.InterventionType.email: "email", m.InterventionType.meeting: "meeting",
            m.InterventionType.academic_counselling: "referral", m.InterventionType.remedial_recommendation: "email",
            m.InterventionType.other: "call"}


def case_out(iv: m.Intervention) -> str:
    if iv.status in (m.InterventionStatus.completed, m.InterventionStatus.cancelled):
        return "resolved"
    if iv.outcome == m.InterventionOutcome.unable_to_contact:
        return "no_response"
    if iv.outcome == m.InterventionOutcome.further_support_required:
        return "escalated"
    return "not_contacted" if iv.status == m.InterventionStatus.open else "in_progress"


def set_case(db: Session, iv: m.Intervention, case: str, user: m.User | None, record_history: bool = True) -> None:
    status, outcome = CASE_IN[case]
    for field, new in (("status", status), ("outcome", outcome)):
        old = getattr(iv, field)
        if old != new:
            if record_history:
                db.add(m.InterventionHistory(
                    intervention_id=iv.id, changed_by=user.id if user else None, field_changed=field,
                    old_value=old.value if old else None, new_value=new.value if new else None))
            setattr(iv, field, new)
    iv.completed_at = m.now_naive() if status == m.InterventionStatus.completed else None


def intervention_out(iv: m.Intervention, slug_of: dict) -> dict:
    d = iv.detail
    follow = None
    if d and d.follow_up_at:
        follow = d.follow_up_at
    elif iv.follow_up_date:
        follow = datetime.combine(iv.follow_up_date, time(12, 0), tzinfo=timezone.utc)
    return {
        "id": str(iv.id), "studentId": str(iv.student_id), "courseId": slug_of.get(d.course_id) if d else None,
        "reason": (d.reason_key if d else None) or "general", "type": TYPE_OUT[iv.intervention_type], "at": iv.created_at,
        "by": str(iv.staff_user_id), "notes": iv.description, "followUp": follow,
        "referralTo": str(d.referral_to_user_id) if d and d.referral_to_user_id else None, "outcome": case_out(iv),
    }


def load_interventions(db: Session, student_id: uuid.UUID | None = None) -> list[dict]:
    slug_of = {c.id: c.slug for c in db.scalars(select(m.Course)).all()}
    q = select(m.Intervention).order_by(m.Intervention.created_at)
    if student_id:
        q = q.where(m.Intervention.student_id == student_id)
    return [intervention_out(iv, slug_of) for iv in db.scalars(q).all()]


# ---------- Imports, jobs, users ----------

IMPORT_LABEL = {m.ImportType.course_results: "Term results", m.ImportType.registrations: "Course registrations",
                m.ImportType.assessment_scores: "Weekly assignment scores", m.ImportType.students: "Students",
                m.ImportType.projects: "Project stages"}
IMPORT_STATUS = {m.ImportStatus.committed: "succeeded", m.ImportStatus.failed: "failed",
                 m.ImportStatus.pending: "pending", m.ImportStatus.validated: "pending"}


def import_out(row: m.DataImport, names: dict) -> dict:
    terms = row.validated_rows.get("terms", []) if isinstance(row.validated_rows, dict) else []
    return {"id": str(row.id), "file": row.filename, "category": IMPORT_LABEL[row.import_type], "term": ", ".join(terms) or "None",
            "rows": row.total_rows, "accepted": row.successful_rows, "rejected": row.failed_rows,
            "status": IMPORT_STATUS[row.status], "at": utc(row.completed_at or row.created_at),
            "by": names.get(row.uploaded_by, "System")}


def job_out(row: m.SystemJob) -> dict:
    return {"id": str(row.id), "name": row.name, "detail": row.detail or "", "status": row.status, "at": row.run_at}


def account_out(u: m.User) -> dict:
    return {"id": str(u.id), "email": u.email, "name": u.full_name, "role": ROLE_OUT[u.role],
            "title": u.staff_profile.title if u.staff_profile else "", "active": u.is_active}


def user_names(db: Session) -> dict:
    return {uid: name for uid, name in db.execute(select(m.User.id, m.User.full_name)).all()}
