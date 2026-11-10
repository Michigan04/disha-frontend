"""Demo data that the pages used to hard-code, now kept in the database.

ensure_extras() adds whatever is missing and never overwrites, so it runs both for
a fresh database (after seeding) and for one seeded before these existed
(`python -m app.bootstrap`).

- prediction_model (policy setting): model version and last term's accuracy
- ai_review_samples (policy setting): sample student messages the admin reviews
- course_content kind "outcomes": last term's results by component, per course
- risk_snapshots: weekly counts per risk level for the active term (Overview trend)
"""
from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from . import records

PREDICTION_MODEL = {"name": "Score prediction model", "version": "0.3", "accuracy": 0.81, "measuredOn": "May 2026"}

AI_REVIEW_SAMPLES = [
    {"id": 1, "to": "A Low-risk student, Statistics II", "flagged": False,
     "text": "You are close to passing Statistics II. Students who passed after one failed attempt usually did two "
             "timed past papers before each quiz. This week, try the Week 7 practice set."},
    {"id": 2, "to": "A High-risk student, Python", "flagged": False,
     "text": "Your OPPE 1 eligibility depends on your weekly assignment average. Weeks 8 and 9 still count towards "
             "OPPE 2, so submitting both can make you eligible."},
]

# Share of last term's students who reached each mark (sample figures).
LAST_TERM_OUTCOMES = [
    {"label": "Weekly assignments (40 or more)", "pct": 82},
    {"label": "Quiz 1 (40 or more)", "pct": 71},
    {"label": "OPPE 1 passed", "pct": 58},
    {"label": "OPPE 2 passed", "pct": 64},
    {"label": "End-term exam (40 or more)", "pct": 73},
]

# How far each earlier week's counts were from this week's (sample history):
# index 0 = last week, 1 = two weeks ago, ...
LOW_BEFORE = [1, 2, 2, 3, 4, 4]
HIGH_BEFORE = [2, 2, 2, 2, 3, 3]


def ensure_extras(db: Session) -> list[str]:
    added = []
    if records.get_setting(db, "prediction_model") is None:
        records.set_setting(db, "prediction_model", PREDICTION_MODEL, description="Score prediction model shown on Data and system")
        added.append("prediction_model")
    if records.get_setting(db, "ai_review_samples") is None:
        records.set_setting(db, "ai_review_samples", AI_REVIEW_SAMPLES, description="Sample student messages for AI review")
        added.append("ai_review_samples")

    have = set(db.scalars(select(m.CourseContent.course_id).where(m.CourseContent.kind == "outcomes")).all())
    courses = db.scalars(select(m.Course).where(m.Course.is_active)).all()
    missing = [c for c in courses if c.id not in have]
    for c in missing:
        db.add(m.CourseContent(course_id=c.id, kind="outcomes", data={"term": "May 2026", "parts": LAST_TERM_OUTCOMES}))
    if missing:
        added.append(f"outcomes for {len(missing)} courses")

    if _seed_snapshots(db):
        added.append("risk_snapshots")
    db.flush()
    return added


def _seed_snapshots(db: Session) -> bool:
    """Fill in earlier weeks of the active term that have no snapshot yet."""
    term = db.scalar(select(m.AcademicTerm).where(m.AcademicTerm.is_active))
    if term is None:
        return False
    week = int(records.get_setting(db, "current_week", 1) or 1)
    have = set(db.scalars(select(m.RiskSnapshot.week).where(m.RiskSnapshot.term_id == term.id)).all())
    todo = [w for w in range(1, week + 1) if w not in have]
    if not todo:
        return False
    latest = db.scalars(select(m.RiskAssessment.risk_level).distinct(m.RiskAssessment.student_id)
                        .order_by(m.RiskAssessment.student_id, m.RiskAssessment.assessment_date.desc())).all()
    if not latest:
        return False
    now = Counter(records.RISK_OUT[lv] for lv in latest)
    total = sum(now.values())
    for w in todo:
        back = week - w
        low = now["low"] + (LOW_BEFORE[min(back, 6) - 1] if back else 0)
        high = max(0, now["high"] - (HIGH_BEFORE[min(back, 6) - 1] if back else 0))
        counts = {"high": high, "low": low, "none": max(0, total - high - low)}
        for level, n in counts.items():
            db.add(m.RiskSnapshot(term_id=term.id, week=w, level=records.RISK_IN[level], students=n))
    return True
