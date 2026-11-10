"""Reads the database into the shapes the frontend works with.

Everything here loads in bulk (a fixed number of queries whatever the cohort size).
Ids sent to the browser: students and staff use their UUID, courses use their slug.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m

# Frontend role names <-> DBML user_role
ROLE_OUT = {m.UserRole.student: "student", m.UserRole.ta: "support", m.UserRole.faculty: "instructor", m.UserRole.admin: "admin"}
ROLE_IN = {v: k for k, v in ROLE_OUT.items()}

# Frontend risk level <-> DBML risk_level ("low" in the DB means on track)
RISK_OUT = {m.RiskLevel.low: "none", m.RiskLevel.moderate: "low", m.RiskLevel.high: "high", m.RiskLevel.critical: "high"}
RISK_IN = {"none": m.RiskLevel.low, "low": m.RiskLevel.moderate, "high": m.RiskLevel.high}

DEFAULT_TERM_WEEKS = 12


def utc(dt: datetime | None) -> datetime | None:
    """Columns the DBML declares as plain `timestamp` hold UTC; label them so."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ---------- Settings ----------

def get_setting(db: Session, key: str, default=None):
    row = db.scalar(select(m.PolicySetting).where(m.PolicySetting.key == key))
    return default if row is None else row.value


def set_setting(db: Session, key: str, value, user_id=None, description: str | None = None):
    row = db.scalar(select(m.PolicySetting).where(m.PolicySetting.key == key))
    if row is None:
        row = m.PolicySetting(key=key, value=value, description=description, updated_by=user_id)
        db.add(row)
    else:
        row.value = value
        row.updated_by = user_id
        row.updated_at = m.now_naive()
        if description:
            row.description = description
    return row


# ---------- Rules ----------

def milestone_rules(db: Session) -> dict:
    out: dict[str, list] = defaultdict(list)
    rows = db.scalars(select(m.AcademicMilestone).where(m.AcademicMilestone.is_active).order_by(m.AcademicMilestone.sequence_order)).all()
    for r in rows:
        item = {"byTerm": r.by_term, "courses": r.required_courses}
        if r.required_projects is not None:
            item["projects"] = r.required_projects
        out[r.academic_level.value].append(item)
    return dict(out)


def current_rules(db: Session) -> dict:
    """The thresholds in force: failed-attempt rules, OPPE minimum and milestones."""
    latest = db.scalar(select(m.RuleVersion).order_by(m.RuleVersion.version.desc()).limit(1))
    fail_rules = db.scalars(select(m.RiskRule).where(
        m.RiskRule.indicator_type == m.RiskIndicatorType.failed_courses, m.RiskRule.is_active)).all()
    high = next((r for r in fail_rules if r.severity == m.Severity.critical), None)
    low = next((r for r in fail_rules if r.severity == m.Severity.warning), None)
    return {
        "version": latest.version if latest else 1,
        "effective": latest.effective if latest else "",
        "highFails": int(high.threshold_value) if high else 2,
        "lowFails": int(low.threshold_value) if low else 1,
        "oppeMin": get_setting(db, "oppe_min_assignment_avg", 40),
        "milestones": milestone_rules(db),
    }


# ---------- Reference data ----------

def course_out(c: m.Course) -> dict:
    out = {"id": c.slug, "code": c.course_code, "name": c.course_name, "level": c.academic_level.value,
           "type": c.course_type, "credits": c.credits}
    if c.has_oppe:
        out["oppe"] = True
    return out


def staff_out(u: m.User, slug_of: dict) -> dict:
    p = u.staff_profile
    out = {"id": str(u.id), "name": u.full_name, "email": u.email, "role": ROLE_OUT[u.role], "title": p.title if p else None}
    if p and p.capacity is not None:
        out["capacity"] = p.capacity
    if p and p.course_id:
        out["courseId"] = slug_of.get(p.course_id)
    return out


def reference(db: Session) -> dict:
    """Catalogue, program rules and course content: what every page needs to draw itself."""
    courses = db.scalars(select(m.Course).where(m.Course.is_active).order_by(m.Course.sequence_order)).all()
    slug_of = {c.id: c.slug for c in courses}
    level_courses: dict[str, list] = defaultdict(list)
    for c in courses:
        level_courses[c.academic_level.value].append(c.slug)

    content: dict[str, dict] = {"guide": {}, "plan": {}, "insight": {}, "scheme": {}}
    for row in db.scalars(select(m.CourseContent)).all():
        if row.course_id in slug_of:
            content.setdefault(row.kind, {})[slug_of[row.course_id]] = row.data

    ms = milestone_rules(db)
    level_rules = {}
    for level, rule in (get_setting(db, "level_rules", {}) or {}).items():
        level_rules[level] = {**rule, "milestones": ms.get(level, [])}

    staff = db.scalars(select(m.User).where(m.User.role != m.UserRole.student, m.User.is_active)).all()
    return {
        "courses": {c.slug: course_out(c) for c in courses},
        "levelCourses": dict(level_courses),
        "gradePoints": get_setting(db, "grade_points", {}),
        "gradeBands": get_setting(db, "grade_bands", []),
        "levelRules": level_rules,
        "riskRules": get_setting(db, "risk_labels", {}),
        "permissions": get_setting(db, "permissions", []),
        "suggestedActions": get_setting(db, "suggested_actions", {}),
        "schemes": content["scheme"],
        "defaultScheme": get_setting(db, "default_scheme", None),
        "defaultOppeScheme": get_setting(db, "default_oppe_scheme", None),
        "guides": content["guide"],
        "plans": content["plan"],
        "insights": content["insight"],
        "staff": {str(u.id): staff_out(u, slug_of) for u in staff},
    }


# ---------- Student records ----------

def _in(col, ids):
    return col.in_(ids) if ids is not None else True


def load_students(db: Session, student_ids: list[uuid.UUID] | None = None) -> list[dict]:
    """Student records in the frontend's shape: attempts, OPPEs, meetings, instructor support."""
    q = select(m.Student).order_by(m.Student.created_at, m.Student.student_identifier)
    if student_ids is not None:
        q = q.where(m.Student.id.in_(student_ids))
    students = db.scalars(q).all()
    if not students:
        return []
    ids = [s.id for s in students] if student_ids is not None else None

    terms = db.scalars(select(m.AcademicTerm).order_by(m.AcademicTerm.start_date)).all()
    term_by_id = {t.id: t for t in terms}
    term_names = [t.name for t in terms]
    active = next((t for t in terms if t.is_active), terms[-1] if terms else None)
    active_idx = term_names.index(active.name) if active else -1
    courses = {c.id: c for c in db.scalars(select(m.Course)).all()}
    weeks = get_setting(db, "term_weeks", DEFAULT_TERM_WEEKS)
    current_week = get_setting(db, "current_week", 1)

    results = defaultdict(list)
    for r in db.scalars(select(m.CourseResult).where(_in(m.CourseResult.student_id, ids))).all():
        results[r.student_id].append(r)

    regs = defaultdict(list)
    first_term = {}
    for r in db.scalars(select(m.Registration).where(
            _in(m.Registration.student_id, ids), m.Registration.status == m.RegistrationStatus.approved,
    ).order_by(m.Registration.created_at)).all():
        idx = term_names.index(term_by_id[r.academic_term_id].name)
        first_term[r.student_id] = min(first_term.get(r.student_id, idx), idx)
        if active and r.academic_term_id == active.id:
            regs[r.student_id].append(r)

    scores = defaultdict(lambda: defaultdict(list))
    if active:
        for sc in db.scalars(select(m.AssessmentScore).where(
                _in(m.AssessmentScore.student_id, ids), m.AssessmentScore.academic_term_id == active.id)).all():
            scores[sc.student_id][sc.course_id].append(sc)

    oppe = defaultdict(list)
    if active:
        rows = db.execute(select(m.OppeEligibility, m.OppeExam).join(m.OppeExam, m.OppeExam.id == m.OppeEligibility.oppe_exam_id).where(
            _in(m.OppeEligibility.student_id, ids), m.OppeExam.academic_term_id == active.id).order_by(m.OppeExam.exam_date)).all()
        for el, exam in rows:
            item = {"id": str(el.id), "courseId": courses[exam.course_id].slug, "title": exam.title,
                    "date": exam.exam_date, "criteria": [_criterion(c) for c in el.criteria]}
            if el.if_not_eligible:
                item["ifNotEligible"] = el.if_not_eligible
            oppe[el.student_id].append(item)

    user_ids = [s.user_id for s in students]
    since = datetime.combine(datetime.now(timezone.utc).date() - timedelta(days=1), time.min, tzinfo=timezone.utc)
    meetings = defaultdict(list)
    for mt in db.scalars(select(m.Meeting).where(m.Meeting.user_id.in_(user_ids), m.Meeting.end_at >= since).order_by(m.Meeting.start_at)).all():
        meetings[mt.user_id].append(meeting_out(mt))

    support = _support_cards(db, ids, courses)

    out = []
    for s in students:
        res = sorted(results[s.id], key=lambda r: (term_by_id[r.academic_term_id].start_date, courses[r.course_id].sequence_order))
        attempts = []
        graded_now = set()
        idxs = [first_term[s.id]] if s.id in first_term else []
        for r in res:
            term = term_by_id[r.academic_term_id]
            idxs.append(term_names.index(term.name))
            if r.result_status in (m.ResultStatus.pass_, m.ResultStatus.fail) and r.grade:
                attempts.append({"courseId": courses[r.course_id].slug, "term": term.name, "grade": r.grade})
                if active and term.id == active.id:
                    graded_now.add(r.course_id)
        for reg in regs[s.id]:
            if reg.course_id in graded_now:
                continue
            course = courses[reg.course_id]
            a = {"courseId": course.slug, "term": active.name, "inProgress": True, "week": current_week, "weeks": weeks}
            sc = scores[s.id][reg.course_id]
            assignments = [x for x in sc if x.kind == "assignment"]
            if assignments:
                a["assignmentAvg"] = _round(sum(float(x.score) for x in assignments) / len(assignments))
                a["week"] = max(current_week, max(x.week for x in assignments))
            for x in sc:
                if x.kind != "assignment":
                    a[x.kind] = _num(x.score)
            attempts.append(a)

        # Terms at this level: every term from the first one on record to the current term.
        start = min(idxs) if idxs else active_idx
        term_list = term_names[start:active_idx + 1] if active_idx >= 0 else []
        latest = max([r.recorded_at for r in res] + [x.recorded_at for by_course in scores[s.id].values() for x in by_course] + [s.updated_at])
        rec = {
            "id": str(s.id),
            "name": s.full_name,
            "firstName": s.full_name.split(" ")[0],
            "rollNo": s.student_identifier,
            "level": s.academic_level.value,
            "program": s.program_name or "",
            "terms": term_list,
            "admittedFrom": s.admitted_term or (term_list[0] if term_list else ""),
            "combinedLimit": None,
            "updatedAt": latest,
            "attempts": attempts,
            "oppe": oppe[s.id],
            "meetings": meetings[s.user_id],
        }
        if s.id in support:
            rec["intervention"] = support[s.id]
        out.append(rec)
    return out


def _round(x: float) -> int:
    import math
    return math.floor(x + 0.5)


def _num(x):
    f = float(x)
    return int(f) if f == int(f) else f


def _criterion(c: dict) -> dict:
    out = dict(c)
    if out.get("finalOn"):
        out["finalOn"] = datetime.fromisoformat(out["finalOn"])
    return out


def meeting_out(mt: m.Meeting) -> dict:
    out = {"id": str(mt.id), "title": mt.title, "start": mt.start_at, "end": mt.end_at, "link": mt.link or "", "organizer": mt.organizer or ""}
    if mt.location:
        out["location"] = mt.location
    if mt.is_important:
        out["important"] = True
    return out


def _support_cards(db: Session, ids, courses) -> dict:
    """The open instructor-support plan for a student, shown on their course page."""
    rows = db.execute(
        select(m.Intervention, m.InterventionDetail, m.User)
        .join(m.InterventionDetail, m.InterventionDetail.intervention_id == m.Intervention.id)
        .join(m.User, m.User.id == m.Intervention.staff_user_id)
        .where(_in(m.Intervention.student_id, ids), m.InterventionDetail.support_plan.is_not(None),
               m.Intervention.status.in_([m.InterventionStatus.open, m.InterventionStatus.in_progress]))
        .order_by(m.Intervention.created_at)
    ).all()
    out = {}
    for iv, d, user in rows:
        plan = d.support_plan or {}
        if not plan.get("plan"):
            continue
        out[iv.student_id] = {
            "courseId": courses[d.course_id].slug if d.course_id else None,
            "instructor": user.full_name,
            "role": user.staff_profile.title if user.staff_profile else "",
            "status": plan.get("status", "In progress"),
            "meetingAt": d.follow_up_at,
            "link": plan.get("link", ""),
            "reason": plan.get("reason", ""),
            "plan": plan.get("plan", []),
        }
    return out


# ---------- Staff-only details per student ----------

def load_meta(db: Session, students: list[dict], rules: dict, ref: dict) -> dict:
    from . import academics

    by_id = {uuid.UUID(s["id"]): s for s in students}
    ids = list(by_id)
    rows = {s.id: s for s in db.scalars(select(m.Student).where(m.Student.id.in_(ids))).all()}
    slug_to_id = {c.slug: c.id for c in db.scalars(select(m.Course)).all()}

    history = defaultdict(list)
    for a in db.scalars(select(m.StudentAssignment).where(m.StudentAssignment.student_id.in_(ids)).order_by(m.StudentAssignment.assigned_at)).all():
        history[a.student_id].append({"owner": str(a.staff_user_id), "at": utc(a.assigned_at), "by": str(a.assigned_by) if a.assigned_by else None, "reason": a.reason or ""})

    assessments = defaultdict(list)
    for a in db.scalars(select(m.RiskAssessment).where(m.RiskAssessment.student_id.in_(ids)).order_by(m.RiskAssessment.assessment_date)).all():
        assessments[a.student_id].append(a)

    ticks = defaultdict(lambda: defaultdict(list))
    for t in db.scalars(select(m.StudyPlanProgress).where(
            m.StudyPlanProgress.student_id.in_(ids), m.StudyPlanProgress.task_key != "_started")).all():
        ticks[t.student_id][t.course_id].append(t.done_at)

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    out = {}
    for sid, s in by_id.items():
        hist = assessments[sid]
        current = RISK_OUT[hist[-1].risk_level] if hist else "none"
        # When the present run at this level began, and the level a week ago.
        flagged = None
        if hist and current != "none":
            for a in reversed(hist):
                if RISK_OUT[a.risk_level] != current:
                    break
                flagged = a.assessment_date
        older = [a for a in hist if a.assessment_date <= week_ago]
        prev = RISK_OUT[older[-1].risk_level] if older else (RISK_OUT[hist[0].risk_level] if hist else current)

        plan = None
        rk = academics.risk_with(s, rules, ref)
        if rk["level"] == "low":
            focus = rk["focus"]["course"]["id"]
            done = ticks[sid].get(slug_to_id.get(focus), [])
            total = sum(len(w.get("tasks", [])) for w in ref["plans"].get(focus, {}).get("weeks", [])) or 36
            last = max(done) if done else flagged
            if last:
                plan = {"done": len(done), "total": total, "lastActive": last}

        owner = rows[sid].assigned_staff_id
        out[s["id"]] = {
            "owner": str(owner) if owner else None,
            "flaggedOn": flagged,
            "prevLevel": prev,
            "dataIssue": hist[-1].data_completeness_note if hist else None,
            "plan": plan,
            "ownerHistory": history[sid],
        }
    return out
