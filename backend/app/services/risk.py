"""Risk engine: works out every student's risk level from the rules in force and
stores it as a risk assessment with its factors (DBML tables risk_assessments and
risk_factors). Also keeps student_milestones in step and alerts staff about new
High-risk students.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from . import academics, records

# Points each kind of reason adds to the 0-100 risk score.
POINTS = {"failed_twice": 60, "failed_once": 30, "oppe_not_eligible": 10, "low_prediction": 10,
          "behind_milestone": 10, "plan_inactive": 5, "data_issue": 0}
SEVERITY = {"failed_twice": m.Severity.critical, "failed_once": m.Severity.warning, "oppe_not_eligible": m.Severity.warning,
            "low_prediction": m.Severity.warning, "behind_milestone": m.Severity.warning,
            "plan_inactive": m.Severity.info, "data_issue": m.Severity.info}
LEVEL_LABEL = {"high": "High risk", "low": "Low risk", "none": "On track"}


def _rules_by_reason(db: Session) -> dict:
    rules = db.scalars(select(m.RiskRule).where(m.RiskRule.is_active)).all()
    out = {}
    for r in rules:
        if r.indicator_type == m.RiskIndicatorType.failed_courses:
            out["failed_twice" if r.severity == m.Severity.critical else "failed_once"] = r
        elif r.indicator_type == m.RiskIndicatorType.missed_milestone:
            out["behind_milestone"] = r
        elif r.indicator_type == m.RiskIndicatorType.inactivity:
            out["plan_inactive"] = r
    return out


def _data_note(student: dict, ref: dict, previous: str | None) -> str | None:
    """Flag records that look incomplete. A note raised by hand stays until it is cleared."""
    quiz = "Quiz 1 score missing for the current term"
    if previous and previous != quiz:
        return previous
    for a in student["attempts"]:
        if a.get("inProgress") and ref["courses"][a["courseId"]]["type"] == "course":
            if a.get("assignmentAvg") is not None and a.get("quiz1") is None and a.get("week", 0) >= 7:
                return quiz
    return None


def recalculate(db: Session, when=None) -> list[dict]:
    """Assess every student. Returns the students whose level changed."""
    ref = records.reference(db)
    rules = records.current_rules(db)
    students = records.load_students(db)
    meta = records.load_meta(db, students, rules, ref)
    rule_for = _rules_by_reason(db)
    actions = ref["suggestedActions"]
    when = when or m.now_tz()

    latest = {}
    for a in db.scalars(select(m.RiskAssessment).order_by(m.RiskAssessment.assessment_date)).all():
        latest[a.student_id] = a
    milestone_rows = db.scalars(select(m.AcademicMilestone).where(m.AcademicMilestone.is_active).order_by(m.AcademicMilestone.sequence_order)).all()
    student_ms = {(x.student_id, x.milestone_id): x for x in db.scalars(select(m.StudentMilestone)).all()}

    changes = []
    for s in students:
        sid = uuid.UUID(s["id"])
        prev = latest.get(sid)
        mt = dict(meta[s["id"]])
        mt["dataIssue"] = _data_note(s, ref, prev.data_completeness_note if prev else None)
        level = academics.risk_with(s, rules, ref)["level"]
        why = academics.reasons(s, mt, rules, ref)

        assessment = m.RiskAssessment(
            student_id=sid, risk_level=records.RISK_IN[level], assessment_date=when,
            assessment_version=f"v{rules['version']}", data_completeness_note=mt["dataIssue"],
            summary=f"{LEVEL_LABEL[level]}. " + ("; ".join(r["text"] for r in why) if why else "No course failed and milestones on schedule."),
            risk_score=Decimal(0),
        )
        score = Decimal(0)
        for r in why:
            rule = rule_for.get(r["key"])
            points = Decimal(POINTS.get(r["key"], 0)) * (rule.weight if rule else Decimal(1))
            score += points
            suggestion = (actions.get(r["key"]) or [{}])[0].get("text")
            assessment.factors.append(m.RiskFactor(
                rule_id=rule.id if rule else None, factor_name=r["key"],
                observed_value=Decimal(str(r["observed"])) if r.get("observed") is not None else None,
                threshold_value=rule.threshold_value if rule else None,
                severity=SEVERITY.get(r["key"], m.Severity.info), explanation=r["text"],
                recommended_action=suggestion, points_contributed=min(points, Decimal(100)),
            ))
        assessment.risk_score = min(score, Decimal(100))
        db.add(assessment)

        before = records.RISK_OUT[prev.risk_level] if prev else None
        if before is not None and before != level:
            changes.append({"id": s["id"], "name": s["name"], "from": before, "to": level})
            if level == "high":
                _alert_new_high(db, sid, s, mt, when)

        _sync_milestones(db, sid, s, rules, ref, milestone_rows, student_ms, when)

    records.set_setting(db, "last_recalculated_at", when.isoformat())
    db.flush()
    return changes


def _alert_new_high(db: Session, sid, student: dict, meta: dict, when) -> None:
    """Tell the case owner (or, with no owner, every administrator) once per day."""
    if meta.get("owner"):
        targets = [uuid.UUID(meta["owner"])]
    else:
        targets = list(db.scalars(select(m.User.id).where(m.User.role == m.UserRole.admin, m.User.is_active)).all())
    for uid in targets:
        key = f"risk_escalation:{sid}:{uid}:{when.date().isoformat()}"
        if db.scalar(select(m.Notification.id).where(m.Notification.dedupe_key == key)):
            continue
        note = m.Notification(
            user_id=uid, student_id=sid, notification_type=m.NotificationType.risk_escalation,
            title=f"{student['name']} moved to High risk",
            message=f"{student['name']} ({student['rollNo']}) is now High risk. Open the profile to see the reasons and log a first contact.",
            severity=m.Severity.critical, dedupe_key=key, created_at=when,
        )
        note.deliveries.append(m.NotificationDelivery(channel=m.DeliveryChannel.in_app, delivery_status=m.DeliveryStatus.sent, attempt_count=1, sent_at=when))
        note.deliveries.append(m.NotificationDelivery(channel=m.DeliveryChannel.email, delivery_status=m.DeliveryStatus.skipped, error_message="Email sending is not configured"))
        db.add(note)


def _sync_milestones(db, sid, student, rules, ref, milestone_rows, student_ms, when) -> None:
    states = academics.milestones(student, ref, rules.get("milestones"))
    mine = [r for r in milestone_rows if r.academic_level.value == student["level"]]
    for row, st in zip(mine, states):
        status = {"met": m.MilestoneStatus.completed, "missed": m.MilestoneStatus.overdue,
                  "due": m.MilestoneStatus.in_progress}.get(st["state"], m.MilestoneStatus.not_started)
        sm = student_ms.get((sid, row.id))
        if sm is None:
            sm = m.StudentMilestone(student_id=sid, milestone_id=row.id, status=status)
            student_ms[(sid, row.id)] = sm
            db.add(sm)
        if sm.status != status or (status == m.MilestoneStatus.completed and sm.completed_at is None):
            sm.status = status
            sm.completed_at = when.replace(tzinfo=None) if status == m.MilestoneStatus.completed else None


# ---------- Changing the rules ----------

def check_rules(nxt: dict, ref: dict) -> list[str]:
    problems = []
    if not nxt["highFails"] > nxt["lowFails"]:
        problems.append("High risk must need more failed attempts than Low risk.")
    if nxt["lowFails"] < 1:
        problems.append("Low risk needs at least one failed attempt.")
    if not 0 <= nxt["oppeMin"] <= 100:
        problems.append("The OPPE threshold must be between 0 and 100.")
    for level, items in nxt["milestones"].items():
        rule = ref["levelRules"].get(level)
        if not rule:
            problems.append(f"Unknown level: {level}.")
            continue
        for i, ms in enumerate(items):
            if ms["byTerm"] > rule["limitTerms"]:
                problems.append(f"{rule['label']}: milestone {i + 1} is after the {rule['limitTerms']}-term limit.")
            if i and (ms["byTerm"] <= items[i - 1]["byTerm"] or ms["courses"] < items[i - 1]["courses"]):
                problems.append(f"{rule['label']}: milestone {i + 1} must come later and need at least as many courses as milestone {i}.")
    return problems


def preview(db: Session, nxt: dict) -> dict:
    """Who would change risk level under the proposed rules. Nothing is saved."""
    ref = records.reference(db)
    now = records.current_rules(db)
    changes = []
    for s in records.load_students(db):
        a, b = academics.risk_with(s, now, ref)["level"], academics.risk_with(s, nxt, ref)["level"]
        if a != b:
            changes.append({"id": s["id"], "name": s["name"], "from": a, "to": b})
    return {"problems": check_rules(nxt, ref), "changes": changes}


def summary_of(rules: dict) -> str:
    low = "once" if rules["lowFails"] == 1 else f"{rules['lowFails']} times"
    high = "twice" if rules["highFails"] == 2 else f"{rules['highFails']} times"
    return f"High: same course failed {high}. Low: failed {low}. OPPE: assignment average {rules['oppeMin']}."


def apply_rules(db: Session, nxt: dict, reason: str, user: m.User | None, when=None) -> dict:
    """Save the new thresholds and milestones as the next rule version."""
    now = records.current_rules(db)
    version = now["version"] + 1
    for r in db.scalars(select(m.RiskRule).where(m.RiskRule.indicator_type == m.RiskIndicatorType.failed_courses, m.RiskRule.is_active)).all():
        r.threshold_value = Decimal(nxt["highFails"] if r.severity == m.Severity.critical else nxt["lowFails"])
    records.set_setting(db, "oppe_min_assignment_avg", nxt["oppeMin"], user.id if user else None)

    for old in db.scalars(select(m.AcademicMilestone).where(m.AcademicMilestone.is_active)).all():
        old.is_active = False  # kept for history; student_milestones still point at them
    for level, items in nxt["milestones"].items():
        for i, ms in enumerate(items):
            projects = ms.get("projects")
            text = f"{ms['courses']} courses" + (f" + {projects} projects" if projects is not None else "")
            db.add(m.AcademicMilestone(
                name=f"{level.capitalize()}: {text} by term {ms['byTerm']}", academic_level=m.AcademicLevel(level),
                description=f"Rules v{version}", sequence_order=i, by_term=ms["byTerm"],
                required_courses=ms["courses"], required_projects=projects,
            ))
    snapshot = {"highFails": nxt["highFails"], "lowFails": nxt["lowFails"], "oppeMin": nxt["oppeMin"], "milestones": nxt["milestones"]}
    row = m.RuleVersion(version=version, effective=nxt.get("effective") or now["effective"], summary=summary_of(nxt),
                        reason=reason, snapshot=snapshot, created_by=user.id if user else None, created_at=when or m.now_tz())
    db.add(row)
    db.flush()
    return {"version": version, "summary": row.summary, "effective": row.effective}
