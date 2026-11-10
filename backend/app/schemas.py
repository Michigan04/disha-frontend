"""Request and response bodies. Field names match what the Vue app sends and reads."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Role = Literal["student", "support", "instructor", "admin"]
CaseStatus = Literal["not_contacted", "in_progress", "no_response", "escalated", "resolved"]
ImportCategory = Literal["results", "registrations", "scores"]


# ---------- Auth ----------

class LoginIn(BaseModel):
    email: str = Field(examples=["admin@disha.demo"])
    password: str = Field(examples=["disha123"])


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: Role
    title: str | None = None
    staffId: str | None = Field(None, description="Same as id, for staff accounts")
    studentId: str | None = Field(None, description="The student record, for student accounts")
    courseId: str | None = Field(None, description="Course slug, for instructors")


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class DemoAccount(BaseModel):
    email: str
    name: str
    role: Role
    note: str = ""


class DemoAccountsOut(BaseModel):
    password: str | None = None
    accounts: list[DemoAccount] = []


# ---------- Student ----------

class StudyPlanIn(BaseModel):
    done: list[str] = Field(description='Ticked task keys, "<week>-<task index>"', examples=[["1-0", "1-1"]])


class StudyPlanOut(BaseModel):
    done: list[str] | None = Field(description="null when the student has never ticked a task")


class RegistrationCheckIn(BaseModel):
    courseIds: list[str] = Field(description="Course slugs", examples=[["stats2", "python"]])
    studentId: str | None = Field(None, description="Staff only: check on behalf of this student")
    term: str | None = Field(None, description="Term name; defaults to the active term", examples=["Sep 2026"])


# ---------- Staff ----------

class AssignIn(BaseModel):
    studentIds: list[str] = Field(min_length=1)
    owner: str = Field(description="Staff user id")
    reason: str = Field(min_length=1)


class InterventionIn(BaseModel):
    studentId: str
    courseId: str | None = None
    reason: str = "general"
    type: Literal["call", "email", "meeting", "referral"]
    at: datetime | None = None
    notes: str = Field(min_length=1)
    referralTo: str | None = None
    followUp: datetime | None = None
    outcome: CaseStatus = "in_progress"


class OutcomeIn(BaseModel):
    outcome: CaseStatus


class SharedIn(BaseModel):
    key: str = Field(description="<reason>:<course>:<action>")
    text: str = ""


# ---------- Rules ----------

class MilestoneRule(BaseModel):
    byTerm: int = Field(ge=1)
    courses: int = Field(ge=0)
    projects: int | None = Field(None, ge=0)


class RulesIn(BaseModel):
    highFails: int = Field(ge=1, examples=[2])
    lowFails: int = Field(ge=0, examples=[1])
    oppeMin: float = Field(examples=[40])
    effective: str | None = Field(None, examples=["Sep 2026"])
    milestones: dict[str, list[MilestoneRule]]


class RulesApplyIn(BaseModel):
    rules: RulesIn
    reason: str = Field(min_length=1)


class RiskChange(BaseModel):
    id: str
    name: str
    from_: str = Field(alias="from")
    to: str
    model_config = {"populate_by_name": True}


class RulesPreviewOut(BaseModel):
    problems: list[str]
    changes: list[RiskChange]


# ---------- Admin ----------

class UserPatch(BaseModel):
    role: Role | None = None
    active: bool | None = None


class UserCreate(BaseModel):
    email: str
    name: str
    password: str = Field(min_length=6)
    role: Literal["support", "instructor", "admin"]
    title: str | None = None
    capacity: int | None = None
    courseId: str | None = Field(None, description="Course slug, for instructors")


class LlmIn(BaseModel):
    enabled: bool


# ---------- Chat ----------

class ChatIn(BaseModel):
    system: str
    messages: list[dict[str, Any]]
    context: dict[str, Any] = {}
    response_schema: dict[str, Any] = {}
