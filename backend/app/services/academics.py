"""Academic calculations on a student record: course status, CGPA, milestones, risk,
OPPE eligibility and the predicted score.

These mirror src/utils/progress.js, predict.js and staff.js in the frontend, so the
numbers the server stores (risk assessments, chatbot context) match what pages show.
A "student record" here is the dict built by services/records.py.
"""
from __future__ import annotations

FAIL_GRADE = "U"
TERM_MONTHS = ["Jan", "May", "Sep"]


def term_after(label: str, steps: int = 1) -> str:
    month, year = label.split(" ")
    i, y = TERM_MONTHS.index(month), int(year)
    for _ in range(steps):
        i += 1
        if i == 3:
            i, y = 0, y + 1
    return f"{TERM_MONTHS[i]} {y}"


def js_round(x: float) -> int:
    """Math.round: halves go up."""
    import math
    return math.floor(x + 0.5)


def is_pass(a: dict) -> bool:
    return not a.get("inProgress") and bool(a.get("grade")) and a["grade"] != FAIL_GRADE


def is_fail(a: dict) -> bool:
    return not a.get("inProgress") and a.get("grade") == FAIL_GRADE


def course_status(student: dict, course_id: str) -> dict:
    attempts = [a for a in student["attempts"] if a["courseId"] == course_id]
    passed = next((a for a in attempts if is_pass(a)), None)
    fails = sum(1 for a in attempts if is_fail(a))
    current = next((a for a in attempts if a.get("inProgress")), None)
    if passed:
        return {"state": "passed", "grade": passed["grade"], "term": passed["term"], "fails": fails}
    if current:
        return {"state": "in_progress", "fails": fails, "current": current}
    if fails:
        return {"state": "not_cleared", "fails": fails}
    return {"state": "not_started", "fails": 0}


def course_list(student: dict, ref: dict) -> list[dict]:
    return [
        {"course": ref["courses"][cid], "status": course_status(student, cid)}
        for cid in ref["levelCourses"].get(student["level"], [])
    ]


def completed(student: dict, ref: dict) -> dict:
    done = [c for c in course_list(student, ref) if c["status"]["state"] == "passed"]
    return {
        "courses": sum(1 for c in done if c["course"]["type"] == "course"),
        "projects": sum(1 for c in done if c["course"]["type"] == "project"),
    }


def cgpa(student: dict, ref: dict) -> float | None:
    passed = [a for a in student["attempts"] if is_pass(a)]
    credits = sum(ref["courses"][a["courseId"]]["credits"] for a in passed)
    if not credits:
        return None
    points = sum(ref["courses"][a["courseId"]]["credits"] * ref["gradePoints"].get(a["grade"], 0) for a in passed)
    return js_round(points / credits * 100) / 100


def milestones(student: dict, ref: dict, milestone_rules: dict | None = None) -> list[dict]:
    rules = (milestone_rules or {}).get(student["level"]) or ref["levelRules"].get(student["level"], {}).get("milestones", [])
    now = len(student["terms"])
    done = completed(student, ref)
    out = []
    for m in rules:
        projects = m.get("projects")
        met = done["courses"] >= m["courses"] and (projects is None or done["projects"] >= projects)
        state = "met" if met else ("missed" if m["byTerm"] < now else "upcoming")
        text = f"{m['courses']} courses" if projects is None else f"{m['courses']} courses + {projects} {'project' if projects == 1 else 'projects'}"
        out.append({**m, "met": met, "state": state, "text": text})
    nxt = next((m for m in out if m["state"] == "upcoming"), None)
    if nxt:
        nxt["state"] = "due"
    return out


def risk_with(student: dict, rules: dict, ref: dict) -> dict:
    """high | low | none, from failed attempts at courses not yet cleared."""
    open_ = [c for c in course_list(student, ref) if c["status"]["state"] != "passed" and c["status"]["fails"] > 0]
    high = [c for c in open_ if c["status"]["fails"] >= rules["highFails"]]
    low = [c for c in open_ if rules["lowFails"] <= c["status"]["fails"] < rules["highFails"]]
    if high:
        return {"level": "high", "courses": high, "focus": high[0]}
    if low:
        return {"level": "low", "courses": low, "focus": low[0]}
    return {"level": "none", "courses": [], "focus": None}


def meets(c: dict) -> bool:
    if isinstance(c.get("required"), bool):
        return c.get("actual") == c["required"]
    return c.get("actual") is not None and c["actual"] >= c["required"]


def oppe_status(item: dict, oppe_min: float | None = None) -> str:
    criteria = item["criteria"]
    if oppe_min is not None:
        criteria = [
            {**c, "required": oppe_min} if isinstance(c.get("required"), (int, float)) and not isinstance(c.get("required"), bool) else c
            for c in criteria
        ]
    if any(c.get("final") and not meets(c) for c in criteria):
        return "not_eligible"
    if any(not c.get("final") for c in criteria):
        return "pending"
    return "eligible"


def current_courses(student: dict, ref: dict) -> list[dict]:
    if not student["terms"]:
        return []
    term = student["terms"][-1]
    return [
        {"attempt": a, "course": ref["courses"][a["courseId"]]}
        for a in student["attempts"]
        if a["term"] == term and a.get("inProgress")
    ]


# ---------- Predicted score ----------

def scheme_for(course: dict, ref: dict) -> dict | None:
    if not course or course["type"] != "course":
        return None
    return ref["schemes"].get(course["id"]) or (ref["defaultOppeScheme"] if course.get("oppe") else ref["defaultScheme"])


def _clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return min(hi, max(lo, v))


def predict(student: dict, course_id: str, attempt: dict, ref: dict) -> dict | None:
    scheme = scheme_for(ref["courses"].get(course_id), ref)
    if not scheme or not attempt.get("inProgress") or attempt.get("assignmentAvg") is None:
        return None
    a, q, adjust = attempt["assignmentAvg"], attempt.get("quiz1"), scheme.get("adjust", 0)
    expected = _clamp(a + adjust - 4 if q is None else 0.55 * a + 0.45 * q + adjust)
    total = 0.0
    for p in scheme["parts"]:
        if p["key"] == "assignments":
            v = a
        elif p["key"] == "quiz1" and q is not None:
            v = q
        elif attempt.get(p["key"]) is not None:
            v = attempt[p["key"]]
        else:
            v = expected
            if p.get("oppe"):
                o = next((x for x in student["oppe"] if x["courseId"] == course_id and x["title"] == p["oppe"]), None)
                if o and oppe_status(o) == "not_eligible":
                    v = 0  # a missed OPPE counts as zero
        total += p["weight"] / 100 * v
    score = js_round(_clamp(total) * 10) / 10
    bands = ref["gradeBands"]
    grade = next(b["grade"] for b in bands if js_round(score) >= b["min"])
    return {"score": score, "grade": grade}


# ---------- Reasons a student is flagged (what staff see) ----------

def reasons(student: dict, meta: dict, rules: dict, ref: dict, today=None) -> list[dict]:
    from datetime import datetime, timezone

    rk = risk_with(student, rules, ref)
    out = []
    for c in rk["courses"]:
        fails = c["status"]["fails"]
        out.append({
            "key": "failed_twice" if fails >= rules["highFails"] else "failed_once",
            "courseId": c["course"]["id"],
            "text": f"Failed {c['course']['name']} {'once' if fails == 1 else f'{fails} times'}",
            "observed": fails,
        })
    for o in student["oppe"]:
        if oppe_status(o, rules.get("oppeMin")) == "not_eligible":
            course = ref["courses"][o["courseId"]]
            out.append({"key": "oppe_not_eligible", "courseId": course["id"], "text": f"Not eligible for {course['name']} {o['title']}"})
    for c in current_courses(student, ref):
        p = predict(student, c["course"]["id"], c["attempt"], ref)
        if p and js_round(p["score"]) < 40:
            out.append({"key": "low_prediction", "courseId": c["course"]["id"], "observed": js_round(p["score"]),
                        "text": f"Predicted {js_round(p['score'])} in {c['course']['name']}, below the pass mark"})
    plan = meta.get("plan")
    if rk["level"] == "low" and plan and plan.get("lastActive"):
        now = today or datetime.now(timezone.utc)
        idle = (now.date() - plan["lastActive"].date()).days
        if idle >= 7:
            out.append({"key": "plan_inactive", "courseId": rk["focus"]["course"]["id"], "observed": idle,
                        "text": f"Study plan not opened for {idle} days"})
    missed = next((m for m in milestones(student, ref, rules.get("milestones")) if m["state"] == "missed"), None)
    if missed:
        out.append({"key": "behind_milestone", "text": f"Missed the term {missed['byTerm']} milestone ({missed['text']})"})
    if meta.get("dataIssue"):
        out.append({"key": "data_issue", "text": meta["dataIssue"]})
    return out
