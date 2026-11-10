"""What a signed-in user sees about themselves: reference data, their record, meetings."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .. import models as m
from .. import schemas
from ..database import get_db
from ..deps import current_user, require
from ..services import academics, records

router = APIRouter(prefix="/api", tags=["Student"])
student_only = require("student")


def own_student(db: Session, user: m.User) -> m.Student:
    row = db.scalar(select(m.Student).where(m.Student.user_id == user.id))
    if row is None:
        raise HTTPException(404, "No student record is linked to this account.")
    return row


def course_by_slug(db: Session, slug: str) -> m.Course:
    course = db.scalar(select(m.Course).where(m.Course.slug == slug))
    if course is None:
        raise HTTPException(404, f"Unknown course: {slug}")
    return course


@router.get("/reference", tags=["Reference"],
            summary="Course catalogue, program rules, staff directory and course content")
def reference(_: m.User = Depends(current_user), db: Session = Depends(get_db)):
    return records.reference(db)


@router.get("/me/student", summary="The signed-in student's record: attempts, OPPEs, meetings, support")
def my_record(user: m.User = Depends(student_only), db: Session = Depends(get_db)):
    return records.load_students(db, [own_student(db, user).id])[0]


@router.get("/me/risk", summary="The signed-in student's latest stored risk assessment and its factors")
def my_risk(user: m.User = Depends(student_only), db: Session = Depends(get_db)):
    return risk_assessment_out(db, own_student(db, user).id)


def risk_assessment_out(db: Session, student_id: uuid.UUID) -> dict | None:
    a = db.scalar(select(m.RiskAssessment).where(m.RiskAssessment.student_id == student_id)
                  .order_by(m.RiskAssessment.assessment_date.desc()).limit(1))
    if a is None:
        return None
    return {
        "level": records.RISK_OUT[a.risk_level], "dbLevel": a.risk_level.value, "score": float(a.risk_score),
        "assessedAt": a.assessment_date, "rulesVersion": a.assessment_version, "summary": a.summary,
        "dataNote": a.data_completeness_note,
        "factors": [{"name": f.factor_name, "severity": f.severity.value, "explanation": f.explanation,
                     "observed": float(f.observed_value) if f.observed_value is not None else None,
                     "threshold": float(f.threshold_value) if f.threshold_value is not None else None,
                     "recommendedAction": f.recommended_action, "points": float(f.points_contributed)} for f in a.factors],
    }


@router.get("/me/meetings", tags=["Meetings"], summary="Upcoming meetings for the signed-in user (student or staff)")
def my_meetings(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Meeting).where(m.Meeting.user_id == user.id, m.Meeting.end_at >= m.now_tz())
                      .order_by(m.Meeting.start_at)).all()
    return [records.meeting_out(r) for r in rows]


STARTED = "_started"  # marker row: the student has saved this plan at least once


@router.get("/me/study-plan/{course_id}", response_model=schemas.StudyPlanOut, summary="Ticked study-plan tasks for a course")
def get_plan(course_id: str, user: m.User = Depends(student_only), db: Session = Depends(get_db)):
    student, course = own_student(db, user), course_by_slug(db, course_id)
    keys = db.scalars(select(m.StudyPlanProgress.task_key).where(
        m.StudyPlanProgress.student_id == student.id, m.StudyPlanProgress.course_id == course.id)).all()
    return {"done": [k for k in keys if k != STARTED] if keys else None}


@router.put("/me/study-plan/{course_id}", response_model=schemas.StudyPlanOut, summary="Save the ticked study-plan tasks for a course")
def save_plan(course_id: str, body: schemas.StudyPlanIn, user: m.User = Depends(student_only), db: Session = Depends(get_db)):
    student, course = own_student(db, user), course_by_slug(db, course_id)
    wanted = {k for k in body.done if len(k) <= 32} | {STARTED}
    have = set(db.scalars(select(m.StudyPlanProgress.task_key).where(
        m.StudyPlanProgress.student_id == student.id, m.StudyPlanProgress.course_id == course.id)).all())
    if have - wanted:
        db.execute(delete(m.StudyPlanProgress).where(
            m.StudyPlanProgress.student_id == student.id, m.StudyPlanProgress.course_id == course.id,
            m.StudyPlanProgress.task_key.in_(have - wanted)))
    for key in wanted - have:
        db.add(m.StudyPlanProgress(student_id=student.id, course_id=course.id, task_key=key))
    db.commit()
    return {"done": sorted(wanted - {STARTED})}


@router.post("/registrations/validate", tags=["Registrations"],
             summary="Check a set of courses against level, prerequisites and past results")
def validate_registration(body: schemas.RegistrationCheckIn, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    if records.ROLE_OUT[user.role] == "student":
        student = own_student(db, user)
    else:
        student = db.get(m.Student, uuid.UUID(body.studentId)) if body.studentId else None
        if student is None:
            raise HTTPException(404, "Student not found.")
    term = db.scalar(select(m.AcademicTerm).where(m.AcademicTerm.name == body.term)) if body.term else \
        db.scalar(select(m.AcademicTerm).where(m.AcademicTerm.is_active))
    if term is None:
        raise HTTPException(404, "Term not found.")

    ref = records.reference(db)
    record = records.load_students(db, [student.id])[0]
    best = {}
    for r in db.scalars(select(m.CourseResult).where(m.CourseResult.student_id == student.id)).all():
        best[r.course_id] = max(best.get(r.course_id, 0), float(r.grade_points or 0))
    courses = {c.slug: c for c in db.scalars(select(m.Course)).all()}
    by_id = {c.id: c for c in courses.values()}

    results = []
    for slug in body.courseIds:
        errors = []
        course = courses.get(slug)
        if course is None:
            results.append({"courseId": slug, "valid": False, "errors": ["Unknown course."]})
            continue
        state = academics.course_status(record, slug)["state"] if slug in ref["courses"] else "not_started"
        if course.academic_level != student.academic_level:
            errors.append(f"{course.course_name} is a {course.academic_level.value} course; the student is at {student.academic_level.value} level.")
        if state == "passed":
            errors.append(f"{course.course_name} has already been passed.")
        for p in db.scalars(select(m.CoursePrerequisite).where(m.CoursePrerequisite.course_id == course.id)).all():
            if best.get(p.prerequisite_course_id, 0) < float(p.minimum_grade_points):
                errors.append(f"Prerequisite not met: {by_id[p.prerequisite_course_id].course_name}.")
        results.append({"courseId": slug, "valid": not errors, "errors": errors})

    db.add(m.RegistrationValidationLog(student_id=student.id, academic_term_id=term.id,
                                       requested_courses=body.courseIds, validation_result=results))
    db.commit()
    return {"term": term.name, "valid": all(r["valid"] for r in results), "courses": results}


@router.get("/notifications", tags=["Notifications"], summary="Notifications for the signed-in user, newest first")
def notifications(user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(m.Notification).where(m.Notification.user_id == user.id)
                      .order_by(m.Notification.created_at.desc()).limit(100)).all()
    return [{"id": str(n.id), "type": n.notification_type.value, "title": n.title, "message": n.message,
             "severity": n.severity.value, "read": n.is_read, "studentId": str(n.student_id) if n.student_id else None,
             "at": n.created_at} for n in rows]


@router.post("/notifications/{notification_id}/read", tags=["Notifications"], summary="Mark a notification as read")
def read_notification(notification_id: uuid.UUID, user: m.User = Depends(current_user), db: Session = Depends(get_db)):
    n = db.get(m.Notification, notification_id)
    if n is None or n.user_id != user.id:
        raise HTTPException(404, "Notification not found.")
    n.is_read = True
    db.commit()
    return {"ok": True}
