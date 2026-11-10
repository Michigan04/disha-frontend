"""CSV uploads: check every row, keep the result on the data_imports row, then apply
the accepted rows when the administrator confirms."""
from __future__ import annotations

import csv
import io
import re
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from . import records

CATEGORIES = {
    "results": {"label": "Term results", "type": m.ImportType.course_results,
                "columns": ["roll_no", "course_code", "term", "grade"], "example": ["25f1000101", "BSMA1004", "May 2026", "U"]},
    "registrations": {"label": "Course registrations", "type": m.ImportType.registrations,
                      "columns": ["roll_no", "course_code", "term"], "example": ["25f1000101", "BSMA1004", "Sep 2026"]},
    "scores": {"label": "Weekly assignment scores", "type": m.ImportType.assessment_scores,
               "columns": ["roll_no", "course_code", "term", "week", "score"], "example": ["25f1000101", "BSMA1004", "Sep 2026", "7", "64"]},
}
KEY_OF_TYPE = {c["type"]: key for key, c in CATEGORIES.items()}
TERM_RE = re.compile(r"^(Jan|May|Sep) 20\d\d$")
ROLL_RE = re.compile(r"^\d{2}f\d{7}$")
MAX_ROWS = 50_000


def template(category: str) -> str:
    cat = CATEGORIES[category]
    return f"{','.join(cat['columns'])}\n{','.join(cat['example'])}\n"


def _number(text: str) -> float | None:
    try:
        return float(text)
    except ValueError:
        return None


def validate(db: Session, text: str, category: str) -> dict:
    """Returns {"error": ...} for an unusable file, otherwise accepted and rejected rows."""
    cat = CATEGORIES[category]
    rows = [r for r in csv.reader(io.StringIO(text.lstrip("﻿"))) if any(c.strip() for c in r)]
    if not rows:
        return {"error": "The file is empty."}
    if len(rows) - 1 > MAX_ROWS:
        return {"error": f"The file has more than {MAX_ROWS:,} rows. Split it into smaller files."}
    header = [h.strip().lower() for h in rows[0]]
    missing = [c for c in cat["columns"] if c not in header]
    if missing:
        return {"error": f"Missing column{'s' if len(missing) > 1 else ''}: {', '.join(missing)}. Download the template to see the expected columns."}

    idx = {c: header.index(c) for c in cat["columns"]}
    courses = {c.course_code.upper(): c for c in db.scalars(select(m.Course)).all()}
    students = set(db.scalars(select(m.Student.student_identifier)).all())
    terms_known = set(db.scalars(select(m.AcademicTerm.name)).all())
    grades = set(records.get_setting(db, "grade_points", {}) or {})
    weeks = records.get_setting(db, "term_weeks", records.DEFAULT_TERM_WEEKS)

    seen, accepted, rejected, terms = set(), [], [], []
    for n, r in enumerate(rows[1:]):
        v = {c: (r[idx[c]].strip() if idx[c] < len(r) else "") for c in cat["columns"]}
        code = v["course_code"].upper()
        empty = [c for c in cat["columns"] if v[c] == ""]
        reason = None
        if empty:
            reason = f"Missing {', '.join(empty)}"
        elif not ROLL_RE.match(v["roll_no"]):
            reason = f"Roll number \"{v['roll_no']}\" is not in the expected format"
        elif code not in courses:
            reason = f"Unknown course code {v['course_code']}"
        elif not TERM_RE.match(v["term"]):
            reason = f"Term \"{v['term']}\" should look like Sep 2026"
        elif category == "results" and v["grade"].upper() not in grades:
            reason = f"Grade \"{v['grade']}\" is not one of {', '.join(sorted(grades, key=lambda g: 'SABCDEU'.find(g)))}"
        elif category == "scores" and not (_number(v["week"]) is not None and 1 <= _number(v["week"]) <= weeks and float(v["week"]).is_integer()):
            reason = f"Week {v['week']} is outside 1 to {weeks}"
        elif category == "scores" and not (_number(v["score"]) is not None and 0 <= _number(v["score"]) <= 100):
            reason = f"Score {v['score']} is outside 0 to 100"
        elif v["roll_no"] not in students:
            reason = f"No student has roll number {v['roll_no']}"
        elif v["term"] not in terms_known:
            reason = f"Term {v['term']} is not set up in the system"
        if reason is None:
            key = (v["roll_no"], code, v["term"], v.get("week", ""))
            if key in seen:
                reason = f"Duplicate of an earlier row for the same student, course and {'week' if category == 'scores' else 'term'}"
            seen.add(key)
        if reason:
            rejected.append({"line": n + 2, "reason": reason, "raw": ",".join(r)})
        else:
            course = courses[code]
            accepted.append({**v, "course_code": code, "course": {"id": course.slug, "name": course.course_name}})
            if v["term"] not in terms:
                terms.append(v["term"])
    return {"accepted": accepted, "rejected": rejected, "total": len(rows) - 1, "terms": terms, "category": cat["label"]}


def commit(db: Session, row: m.DataImport) -> int:
    """Apply the accepted rows of a validated import. Returns how many rows were written."""
    category = KEY_OF_TYPE[row.import_type]
    accepted = (row.validated_rows or {}).get("rows", [])
    students = {s.student_identifier: s.id for s in db.scalars(select(m.Student)).all()}
    courses = {c.course_code.upper(): c for c in db.scalars(select(m.Course)).all()}
    terms = {t.name: t for t in db.scalars(select(m.AcademicTerm)).all()}
    points = records.get_setting(db, "grade_points", {}) or {}
    now = m.now_tz()
    week_now = records.get_setting(db, "current_week", 1)

    def ensure_registration(sid, cid, tid):
        reg = db.scalar(select(m.Registration).where(
            m.Registration.student_id == sid, m.Registration.course_id == cid, m.Registration.academic_term_id == tid))
        if reg is None:
            reg = m.Registration(student_id=sid, course_id=cid, academic_term_id=tid)
            db.add(reg)
        reg.status, reg.validation_status = m.RegistrationStatus.approved, m.ValidationStatus.valid

    for v in accepted:
        sid, course, term = students[v["roll_no"]], courses[v["course_code"]], terms[v["term"]]
        if category == "registrations":
            ensure_registration(sid, course.id, term.id)
        elif category == "results":
            ensure_registration(sid, course.id, term.id)
            grade = v["grade"].upper()
            res = db.scalar(select(m.CourseResult).where(
                m.CourseResult.student_id == sid, m.CourseResult.course_id == course.id, m.CourseResult.academic_term_id == term.id))
            if res is None:
                res = m.CourseResult(student_id=sid, course_id=course.id, academic_term_id=term.id, credits=course.credits,
                                     result_status=m.ResultStatus.fail)
                db.add(res)
            res.grade, res.grade_points, res.credits, res.recorded_at = grade, Decimal(str(points.get(grade, 0))), course.credits, now
            res.result_status = m.ResultStatus.pass_ if points.get(grade, 0) > 0 else m.ResultStatus.fail
        else:
            week = int(float(v["week"]))
            sc = db.scalar(select(m.AssessmentScore).where(
                m.AssessmentScore.student_id == sid, m.AssessmentScore.course_id == course.id,
                m.AssessmentScore.academic_term_id == term.id, m.AssessmentScore.kind == "assignment", m.AssessmentScore.week == week))
            if sc is None:
                sc = m.AssessmentScore(student_id=sid, course_id=course.id, academic_term_id=term.id, kind="assignment", week=week, score=0)
                db.add(sc)
            sc.score, sc.recorded_at = Decimal(str(v["score"])), now
            if term.is_active:
                week_now = max(week_now, week)
        db.flush()
    records.set_setting(db, "current_week", week_now)
    row.status = m.ImportStatus.committed
    row.completed_at = m.now_naive()
    return len(accepted)
