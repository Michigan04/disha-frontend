"""First-run data.

Always seeded: terms, the course catalogue, program rules, course content and the
default administrator, so the app is usable as soon as it starts.
With SEED_DEMO_DATA=true (the default) the 60-student demo cohort is added too:
staff accounts, results, scores, OPPEs, meetings, interventions and the audit trail.
Dates in seed/demo_data.json are moved so that the demo is always "this week".

Run by hand:   python -m app.seed            (seeds only an empty database)
               python -m app.seed --reset    (wipes every table first)
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models as m
from .config import BACKEND_DIR, get_settings
from .database import Base, SessionLocal, engine
from .security import store_password
from .services import academics, records, risk, staffdata

DATA_FILE = BACKEND_DIR / "seed" / "demo_data.json"
TERM_STARTS = {"Jan": 1, "May": 5, "Sep": 9}
PREREQUISITES = [("math2", "math1"), ("stats2", "stats1"), ("eng2", "eng1"), ("mad2", "mad1"), ("mad1p", "mad1"), ("mad2p", "mad2")]


def seed_if_empty(db: Session) -> bool:
    if db.scalar(select(func.count()).select_from(m.User)):
        return False
    Seeder(db).run()
    db.commit()
    return True


def term_dates(name: str) -> tuple[date, date]:
    month, year = name.split(" ")
    start = date(int(year), TERM_STARTS[month], 1)
    nxt = date(start.year + (start.month + 4 > 12), (start.month + 4 - 1) % 12 + 1, 1)
    return start, nxt - timedelta(days=1)


class Seeder:
    def __init__(self, db: Session):
        self.db = db
        self.cfg = get_settings()
        self.data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        self.now = datetime.now(timezone.utc)
        self.shift = self.now - self.dt_raw(self.data["generatedAt"])
        self.terms: dict[str, m.AcademicTerm] = {}
        self.courses: dict[str, m.Course] = {}
        self.staff: dict[str, m.User] = {}      # demo key ("neha") -> user
        self.students: dict[str, m.Student] = {}  # demo key ("ananya") -> student
        self.clock = self.now - timedelta(days=400)

    # ----- helpers -----

    @staticmethod
    def dt_raw(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def dt(self, value: str | None) -> datetime | None:
        """A date from the demo file, moved to be relative to now.

        Times that were "in N minutes" when the file was made stay that far from now;
        everything else moves by whole days, so 6:30 pm stays 6:30 pm."""
        if not value:
            return None
        t = self.dt_raw(value)
        ahead = t - self.dt_raw(self.data["generatedAt"])
        if timedelta(0) <= ahead <= timedelta(hours=6):
            moved = (self.now + ahead).replace(second=0, microsecond=0)
            return moved + timedelta(minutes=-moved.minute % 5)
        return t + timedelta(days=round(self.shift / timedelta(days=1)))

    def tick(self) -> datetime:
        """Increasing timestamps, so rows keep the order they were seeded in."""
        self.clock += timedelta(seconds=1)
        return self.clock

    def setting(self, key, value, description=None):
        records.set_setting(self.db, key, value, description=description)

    # ----- run -----

    def run(self) -> None:
        self.reference()
        self.admin_and_staff()
        if self.cfg.seed_demo_data:
            self.demo_students()
            self.db.flush()
            self.assignments_and_interventions()
            self.study_plans()
            self.risk_history()
            self.system_history()
        else:
            self.db.flush()
            risk.recalculate(self.db)

    # ----- reference data -----

    def reference(self) -> None:
        d, db = self.data, self.db
        # Terms from Jan 2024 to the one after today; the term containing today is active.
        name, today = "Jan 2024", self.now.date()
        while True:
            start, end = term_dates(name)
            self.terms[name] = m.AcademicTerm(name=name, start_date=start, end_date=end, is_active=start <= today <= end)
            db.add(self.terms[name])
            if start > today:
                break
            name = academics.term_after(name)

        code_of = {slug: code for code, slug in d["courseCodes"].items()}
        order = [slug for level in d["levelCourses"].values() for slug in level]
        for slug, c in d["courses"].items():
            self.courses[slug] = m.Course(
                slug=slug, course_code=code_of[slug], course_name=c["name"], credits=c["credits"],
                academic_level=m.AcademicLevel(c["level"]), course_type=c["type"], has_oppe=bool(c.get("oppe")),
                sequence_order=order.index(slug))
            db.add(self.courses[slug])
        db.flush()
        for course, needs in PREREQUISITES:
            db.add(m.CoursePrerequisite(course_id=self.courses[course].id, prerequisite_course_id=self.courses[needs].id))

        for kind, key in (("guide", "guides"), ("plan", "plans"), ("insight", "insights"), ("scheme", "schemes")):
            for slug, body in d[key].items():
                db.add(m.CourseContent(course_id=self.courses[slug].id, kind=kind, data=body))

        self.setting("grade_points", d["gradePoints"], "Grade points per letter grade")
        self.setting("grade_bands", d["gradeBands"], "Minimum score for each grade")
        self.setting("level_rules", {lv: {k: v for k, v in r.items() if k != "milestones"} for lv, r in d["levelRules"].items()},
                     "Label, term limit and unit for each level")
        self.setting("risk_labels", d["riskRules"], "How each risk level is described to students")
        self.setting("permissions", d["permissions"], "What each role may do")
        self.setting("suggested_actions", d["suggestedActions"], "Suggested staff actions for each risk reason")
        self.setting("default_scheme", d["defaultScheme"], "Grading scheme for courses without their own")
        self.setting("default_oppe_scheme", d["defaultOppeScheme"], "Grading scheme for OPPE courses without their own")
        self.setting("term_weeks", 12, "Weeks in a term")
        self.setting("current_week", 7, "Week of the active term")
        self.setting("oppe_min_assignment_avg", d["rules"]["oppeMin"], "Assignment average needed to sit an OPPE")
        self.setting("llm_enabled", True, "Language model for student messages")

        for level, items in d["rules"]["milestones"].items():
            for i, ms in enumerate(items):
                projects = ms.get("projects")
                text = f"{ms['courses']} courses" + (f" + {projects} projects" if projects is not None else "")
                db.add(m.AcademicMilestone(name=f"{level.capitalize()}: {text} by term {ms['byTerm']}", academic_level=m.AcademicLevel(level),
                                           sequence_order=i, by_term=ms["byTerm"], required_courses=ms["courses"], required_projects=projects))
        rules = d["rules"]
        db.add(m.RiskRule(name="High risk: same course failed repeatedly", indicator_type=m.RiskIndicatorType.failed_courses,
                          description="Failed attempts at one course that is still not cleared. Instructor support.",
                          threshold_value=rules["highFails"], severity=m.Severity.critical))
        db.add(m.RiskRule(name="Low risk: a course failed", indicator_type=m.RiskIndicatorType.failed_courses,
                          description="Failed attempts at one course that is still not cleared. Guidance from past students.",
                          threshold_value=rules["lowFails"], severity=m.Severity.warning))
        db.add(m.RiskRule(name="Behind a milestone", indicator_type=m.RiskIndicatorType.missed_milestone,
                          description="A milestone's term has passed without the courses it needs.", threshold_value=1, severity=m.Severity.warning))
        db.add(m.RiskRule(name="Study plan not opened", indicator_type=m.RiskIndicatorType.inactivity,
                          description="Days since a Low-risk student last used their study plan.", threshold_value=7, severity=m.Severity.info))
        db.flush()

    def admin_and_staff(self) -> None:
        d, db, cfg = self.data, self.db, self.cfg
        people = d["staff"] if cfg.seed_demo_data else {k: v for k, v in d["staff"].items() if v["role"] == "admin"}
        for key, s in people.items():
            is_admin = s["role"] == "admin"
            user = m.User(
                email=cfg.default_admin_email.lower() if is_admin else f"{key}@disha.demo",
                full_name=cfg.default_admin_name if is_admin else s["name"],
                password_hash=store_password(cfg.default_admin_password if is_admin else cfg.demo_password),
                role=records.ROLE_IN[s["role"]], created_at=self.tick())
            user.staff_profile = m.StaffProfile(title=s.get("title"), capacity=s.get("capacity"),
                                                course_id=self.courses[s["courseId"]].id if s.get("courseId") else None)
            db.add(user)
            self.staff[key] = user
        if cfg.seed_demo_data:
            for u in d["users"]:
                if not u["active"]:
                    gone = m.User(email=u["email"], full_name=u["name"], password_hash=store_password(cfg.demo_password),
                                  role=records.ROLE_IN[u["role"]], is_active=False, created_at=self.tick())
                    gone.staff_profile = m.StaffProfile(title=u.get("title"))
                    db.add(gone)
        db.flush()

        # Rule versions: the last one matches the thresholds seeded above.
        admin = next(u for u in self.staff.values() if u.role == m.UserRole.admin)
        history = d["ruleHistory"] if cfg.seed_demo_data else d["ruleHistory"][-1:]
        for h in history:
            current = h["version"] == d["rules"]["version"]
            snapshot = {"highFails": d["rules"]["highFails"] if current else 3, "lowFails": d["rules"]["lowFails"],
                        "oppeMin": d["rules"]["oppeMin"], "milestones": d["rules"]["milestones"]}
            db.add(m.RuleVersion(version=h["version"], effective=h["effective"], summary=h["summary"], reason=h["reason"],
                                 snapshot=snapshot, created_by=admin.id, created_at=self.dt(h["at"])))

        accounts = []
        if cfg.seed_demo_data:
            for a in d["accounts"]:
                email = cfg.default_admin_email.lower() if a["role"] == "admin" else a["email"]
                name = cfg.default_admin_name if a["role"] == "admin" else a["name"]
                accounts.append({"email": email, "name": name, "role": a["role"], "note": a.get("note", "")})
        self.setting("demo_accounts", accounts, "Accounts offered on the sign-in page while SHOW_DEMO_ACCOUNTS is on")

    # ----- demo cohort -----

    def demo_students(self) -> None:
        d, db = self.data, self.db
        emails = {a["studentId"]: a["email"] for a in d["accounts"] if a.get("studentId")}
        active = next(t for t in self.terms.values() if t.is_active)
        points = d["gradePoints"]
        exams: dict[tuple, m.OppeExam] = {}
        wobble = [3, -2, 1, -4, 2, -1, 1]  # sums to 0: weekly scores that average to the demo figure

        for s in d["students"]:
            user = m.User(email=emails.get(s["id"], f"{s['id']}@disha.demo"), full_name=s["name"],
                          password_hash=store_password(self.cfg.demo_password), role=m.UserRole.student, created_at=self.tick())
            db.add(user)
            db.flush()
            student = m.Student(
                student_identifier=s["rollNo"], user_id=user.id, full_name=s["name"], academic_level=m.AcademicLevel(s["level"]),
                admission_date=term_dates(s["admittedFrom"])[0], current_term=s["terms"][-1], program_name=s["program"],
                admitted_term=s["admittedFrom"], created_at=self.tick(), updated_at=self.dt(s["updatedAt"]))
            db.add(student)
            db.flush()
            self.students[s["id"]] = student

            for a in s["attempts"]:
                course, term = self.courses[a["courseId"]], self.terms[a["term"]]
                db.add(m.Registration(student_id=student.id, course_id=course.id, academic_term_id=term.id,
                                      status=m.RegistrationStatus.approved, validation_status=m.ValidationStatus.valid,
                                      created_at=self.tick()))
                if not a.get("inProgress"):
                    grade = a["grade"]
                    db.add(m.CourseResult(
                        student_id=student.id, course_id=course.id, academic_term_id=term.id, grade=grade,
                        grade_points=Decimal(str(points[grade])), credits=course.credits,
                        result_status=m.ResultStatus.pass_ if points[grade] > 0 else m.ResultStatus.fail,
                        recorded_at=datetime.combine(term.end_date, datetime.min.time(), tzinfo=timezone.utc)))
                    if course.course_type == "project":
                        db.add(m.Project(student_id=student.id, title=course.course_name, status=m.ProjectStatus.completed,
                                         start_date=term.start_date, due_date=term.end_date, completion_date=term.end_date, grade=grade))
                    continue
                if course.course_type == "project":
                    db.add(m.Project(student_id=student.id, title=course.course_name, status=m.ProjectStatus.in_progress,
                                     start_date=term.start_date, due_date=term.end_date))
                recorded = self.dt(s["updatedAt"])
                if a.get("assignmentAvg") is not None:
                    for week in range(1, a["week"] + 1):
                        score = max(0, min(100, a["assignmentAvg"] + wobble[(week - 1) % 7]))
                        db.add(m.AssessmentScore(student_id=student.id, course_id=course.id, academic_term_id=term.id,
                                                 kind="assignment", week=week, score=score, recorded_at=recorded))
                if a.get("quiz1") is not None:
                    db.add(m.AssessmentScore(student_id=student.id, course_id=course.id, academic_term_id=term.id,
                                             kind="quiz1", week=0, score=a["quiz1"], recorded_at=recorded))

            for o in s["oppe"]:
                key = (o["courseId"], o["title"])
                if key not in exams:
                    exams[key] = m.OppeExam(course_id=self.courses[o["courseId"]].id, academic_term_id=active.id,
                                            title=o["title"], exam_date=self.dt(o["date"]))
                    db.add(exams[key])
                    db.flush()
                criteria = [{**c, "finalOn": self.dt(c["finalOn"]).isoformat()} if c.get("finalOn") else c for c in o["criteria"]]
                db.add(m.OppeEligibility(student_id=student.id, oppe_exam_id=exams[key].id, criteria=criteria,
                                         if_not_eligible=o.get("ifNotEligible")))
            for mt in s["meetings"]:
                self.meeting(user.id, mt)

        for key, events in d["staffEvents"].items():
            for mt in events:
                self.meeting(self.staff[key].id, mt)

    def meeting(self, user_id, mt: dict) -> None:
        self.db.add(m.Meeting(user_id=user_id, title=mt["title"], start_at=self.dt(mt["start"]), end_at=self.dt(mt["end"]),
                              link=mt.get("link") or None, organizer=mt.get("organizer"), location=mt.get("location"),
                              is_important=bool(mt.get("important"))))

    def assignments_and_interventions(self) -> None:
        d, db = self.data, self.db
        for key, meta in d["meta"].items():
            student = self.students[key]
            history = meta["ownerHistory"]
            for i, h in enumerate(history):
                last = i == len(history) - 1
                when = self.dt(h["at"]).replace(tzinfo=None)
                db.add(m.StudentAssignment(student_id=student.id, staff_user_id=self.staff[h["owner"]].id,
                                           assigned_by=self.staff[h["by"]].id, assigned_at=when, reason=h["reason"],
                                           is_active=last, unassigned_at=None if last else self.dt(history[i + 1]["at"]).replace(tzinfo=None)))
            if meta["owner"]:
                student.assigned_staff_id = self.staff[meta["owner"]].id

        card = next((s["intervention"] for s in d["students"] if s.get("intervention")), None)
        for i in d["interventions"]:
            status, outcome = staffdata.CASE_IN[i["outcome"]]
            when = self.dt(i["at"])
            follow = self.dt(i["followUp"])
            iv = m.Intervention(
                student_id=self.students[i["studentId"]].id, staff_user_id=self.staff[i["by"]].id,
                intervention_type=staffdata.TYPE_IN[i["type"]], description=i["notes"], status=status, outcome=outcome,
                follow_up_date=follow.date() if follow else None, created_at=when, updated_at=when,
                completed_at=when.replace(tzinfo=None) if status == m.InterventionStatus.completed else None)
            iv.detail = m.InterventionDetail(
                course_id=self.courses[i["courseId"]].id if i.get("courseId") else None, reason_key=i["reason"],
                referral_to_user_id=self.staff[i["referralTo"]].id if i.get("referralTo") else None, follow_up_at=follow)
            # The instructor's support plan the student sees on their course page.
            if card and i["studentId"] == "rahul" and i["by"] == "kavya" and i["type"] == "meeting":
                iv.detail.support_plan = {"status": card["status"], "link": card["link"], "reason": card["reason"], "plan": card["plan"]}
                iv.detail.follow_up_at = self.dt(card["meetingAt"])
            db.add(iv)
        db.flush()

    def study_plans(self) -> None:
        """Ticked study-plan tasks for Low-risk students, up to the count in the demo data."""
        ref = records.reference(self.db)
        rules = records.current_rules(self.db)
        by_id = {s["id"]: s for s in records.load_students(self.db)}
        for key, meta in self.data["meta"].items():
            plan = meta.get("plan")
            if not plan:
                continue
            student = self.students[key]
            focus = academics.risk_with(by_id[str(student.id)], rules, ref)["focus"]
            if not focus:
                continue
            slug = focus["course"]["id"]
            weeks = ref["plans"].get(slug, {}).get("weeks") or [{"w": w, "tasks": [0, 1, 2]} for w in range(1, 13)]
            keys = [f"{w['w']}-{i}" for w in weeks for i in range(len(w["tasks"]))][:plan["done"]]
            when = self.dt(plan["lastActive"])
            for task in ["_started", *keys]:
                self.db.add(m.StudyPlanProgress(student_id=student.id, course_id=self.courses[slug].id, task_key=task, done_at=when))
        self.db.flush()

    def risk_history(self) -> None:
        """Earlier assessments, so "flagged on" and "newly High risk" have a past to read."""
        d, db = self.data, self.db
        ref = records.reference(db)
        rules = records.current_rules(db)
        by_id = {s["id"]: s for s in records.load_students(db)}
        last_run = self.dt(d["jobs"][0]["at"])
        for key, meta in d["meta"].items():
            student = self.students[key]
            level = academics.risk_with(by_id[str(student.id)], rules, ref)["level"]
            flagged = self.dt(meta["flaggedOn"])
            note = meta.get("dataIssue")

            def past(lv, when, text):
                db.add(m.RiskAssessment(student_id=student.id, risk_level=records.RISK_IN[lv], assessment_date=when,
                                        risk_score=Decimal({"high": 60, "low": 30, "none": 0}[lv]), assessment_version="v2",
                                        summary=text, data_completeness_note=note))
            if meta["prevLevel"] != level:
                past(meta["prevLevel"], min(flagged or last_run, last_run) - timedelta(days=30), "Earlier assessment.")
            if flagged and flagged < last_run - timedelta(minutes=30):
                past(level, flagged, "First assessment at this level.")
            elif note:
                past(level, last_run - timedelta(days=10), "Earlier assessment.")
        db.flush()
        risk.recalculate(db, when=last_run)

    def system_history(self) -> None:
        d, db = self.data, self.db
        by_name = {u.full_name: u for u in self.staff.values()}
        by_name[self.data["staff"]["suresh"]["name"]] = self.staff["suresh"]
        label_type = {v: k for k, v in staffdata.IMPORT_LABEL.items()}
        for i in d["imports"]:
            when = self.dt(i["at"]).replace(tzinfo=None)
            db.add(m.DataImport(uploaded_by=by_name[i["by"]].id, filename=i["file"], import_type=label_type[i["category"]],
                                status=m.ImportStatus.committed, total_rows=i["rows"], successful_rows=i["accepted"],
                                failed_rows=i["rejected"], created_at=when, completed_at=when,
                                validated_rows={"terms": [i["term"]], "rows": []}, row_errors=[]))
        for j in d["jobs"]:
            db.add(m.SystemJob(name=j["name"], detail=j["detail"], status=j["status"], run_at=self.dt(j["at"])))
        for a in d["audit"]:
            sid = self.students[a["studentId"]].id if a.get("studentId") else None
            staffdata.audit(db, by_name.get(a["who"]), a["action"], a["details"], sid, at=self.dt(a["at"]))


def reset() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset()
    with SessionLocal() as session:
        print("Seeded." if seed_if_empty(session) else "The database already has users; nothing was seeded. Use --reset to start over.")
