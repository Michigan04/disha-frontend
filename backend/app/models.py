"""Database models.

Part 1 follows the team's DBML design (DB_Diagram_DBML_Code.txt) table for table.
Part 2 holds the extensions the frontend needs that the diagram does not model:
weekly scores, OPPE eligibility, meetings, study-plan ticks, course content,
rule versions and system jobs. Extension columns added to DBML tables are marked
"extension" where they are declared.
"""
import enum
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON, Boolean, Date, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now_tz() -> datetime:
    return datetime.now(timezone.utc)


def now_naive() -> datetime:
    """UTC without tzinfo, for the columns the DBML declares as plain `timestamp`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


TZ = DateTime(timezone=True)
UUID_PK = lambda: mapped_column(primary_key=True, default=uuid.uuid4)  # noqa: E731


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)
    updated_at: Mapped[datetime] = mapped_column(TZ, default=now_tz, onupdate=now_tz)


# ---------- Enums ----------

class UserRole(enum.Enum):
    student = "student"
    faculty = "faculty"
    ta = "ta"
    admin = "admin"


class AcademicLevel(enum.Enum):
    foundation = "foundation"
    diploma = "diploma"
    degree = "degree"


class ProgramStatus(enum.Enum):
    active = "active"
    on_hold = "on_hold"
    completed = "completed"
    discontinued = "discontinued"


class RegistrationStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class ValidationStatus(enum.Enum):
    valid = "valid"
    invalid = "invalid"
    not_validated = "not_validated"


class ResultStatus(enum.Enum):
    pass_ = "pass"  # SQLAlchemy stores the member name, "pass_"
    fail = "fail"
    incomplete = "incomplete"
    withdrawn = "withdrawn"


class MilestoneStatus(enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    overdue = "overdue"


class ProjectStatus(enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    submitted = "submitted"
    completed = "completed"
    overdue = "overdue"


class RiskLevel(enum.Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class Severity(enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class NotificationType(enum.Enum):
    failure_alert = "failure_alert"
    risk_escalation = "risk_escalation"
    intervention_followup = "intervention_followup"
    registration_result = "registration_result"
    general = "general"


class DeliveryChannel(enum.Enum):
    in_app = "in_app"
    email = "email"


class DeliveryStatus(enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"
    skipped = "skipped"


class InterventionType(enum.Enum):
    call = "call"
    email = "email"
    meeting = "meeting"
    academic_counselling = "academic_counselling"
    remedial_recommendation = "remedial_recommendation"
    other = "other"


class InterventionStatus(enum.Enum):
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class InterventionOutcome(enum.Enum):
    improved = "improved"
    no_change = "no_change"
    further_support_required = "further_support_required"
    unable_to_contact = "unable_to_contact"


class ImportType(enum.Enum):
    students = "students"
    course_results = "course_results"
    registrations = "registrations"
    projects = "projects"
    assessment_scores = "assessment_scores"  # extension: weekly assignment scores


class ImportStatus(enum.Enum):
    pending = "pending"
    validated = "validated"
    committed = "committed"
    failed = "failed"


class RiskIndicatorType(enum.Enum):
    low_cgpa = "low_cgpa"
    failed_courses = "failed_courses"
    insufficient_credits = "insufficient_credits"
    missed_milestone = "missed_milestone"
    pending_courses = "pending_courses"
    incomplete_project = "incomplete_project"
    registration_failures = "registration_failures"
    inactivity = "inactivity"
    overdue_followup = "overdue_followup"


def pg_enum(cls, name):
    return Enum(cls, name=name)


# =====================================================================
# Part 1: tables from the DBML design
# =====================================================================

# ---------- Users and students ----------

class User(Base, Timestamps):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = UUID_PK()
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole, "user_role"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    staff_profile: Mapped["StaffProfile | None"] = relationship(back_populates="user", uselist=False)
    student: Mapped["Student | None"] = relationship(back_populates="user", uselist=False, foreign_keys="Student.user_id")


class Student(Base, Timestamps):
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_academic_level", "academic_level"),
        Index("ix_students_assigned_staff", "assigned_staff_id"),
    )
    id: Mapped[uuid.UUID] = UUID_PK()
    student_identifier: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    academic_level: Mapped[AcademicLevel] = mapped_column(pg_enum(AcademicLevel, "academic_level"))
    program_status: Mapped[ProgramStatus] = mapped_column(pg_enum(ProgramStatus, "program_status"), default=ProgramStatus.active)
    admission_date: Mapped[date] = mapped_column(Date)
    current_term: Mapped[str | None] = mapped_column(String(64))
    assigned_staff_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    # extension
    program_name: Mapped[str | None] = mapped_column(String(255))
    admitted_term: Mapped[str | None] = mapped_column(String(64))

    user: Mapped[User] = relationship(back_populates="student", foreign_keys=[user_id])


class StudentAssignment(Base):
    __tablename__ = "student_assignments"
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    staff_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=now_naive)
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text)  # extension


# ---------- Academics ----------

class AcademicTerm(Base):
    __tablename__ = "academic_terms"
    id: Mapped[uuid.UUID] = UUID_PK()
    name: Mapped[str] = mapped_column(String(64), unique=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[uuid.UUID] = UUID_PK()
    course_code: Mapped[str] = mapped_column(String(32), unique=True)
    course_name: Mapped[str] = mapped_column(String(255))
    credits: Mapped[int] = mapped_column(Integer)
    academic_level: Mapped[AcademicLevel] = mapped_column(pg_enum(AcademicLevel, "academic_level"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # extension: short id used in URLs, course or project, has OPPEs, order within the level
    slug: Mapped[str] = mapped_column(String(32), unique=True)
    course_type: Mapped[str] = mapped_column(String(16), default="course")
    has_oppe: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (UniqueConstraint("course_id", "prerequisite_course_id", name="uq_course_prereq"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    prerequisite_course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    minimum_grade_points: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=Decimal("4.0"))


class Registration(Base, Timestamps):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "academic_term_id", name="uq_registration_student_course_term"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    academic_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id"))
    status: Mapped[RegistrationStatus] = mapped_column(pg_enum(RegistrationStatus, "registration_status"), default=RegistrationStatus.pending)
    validation_status: Mapped[ValidationStatus] = mapped_column(pg_enum(ValidationStatus, "validation_status"), default=ValidationStatus.not_validated)
    validation_errors: Mapped[list | dict | None] = mapped_column(JSON)


class RegistrationValidationLog(Base, Timestamps):
    __tablename__ = "registration_validation_logs"
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    academic_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id"))
    requested_courses: Mapped[list | dict] = mapped_column(JSON)
    validation_result: Mapped[list | dict] = mapped_column(JSON)


class CourseResult(Base):
    __tablename__ = "course_results"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "academic_term_id", name="uq_result_student_course_term"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    academic_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id"))
    grade: Mapped[str | None] = mapped_column(String(4))
    grade_points: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    credits: Mapped[int] = mapped_column(Integer)
    result_status: Mapped[ResultStatus] = mapped_column(pg_enum(ResultStatus, "result_status"))
    recorded_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)


# ---------- Milestones and projects ----------

class AcademicMilestone(Base):
    __tablename__ = "academic_milestones"
    id: Mapped[uuid.UUID] = UUID_PK()
    name: Mapped[str] = mapped_column(String(255))
    academic_level: Mapped[AcademicLevel] = mapped_column(pg_enum(AcademicLevel, "academic_level"))
    description: Mapped[str | None] = mapped_column(Text)
    required_credits: Mapped[int | None] = mapped_column(Integer)
    target_cgpa: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    sequence_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # extension: "N courses (+ M projects) by term T"
    by_term: Mapped[int | None] = mapped_column(Integer)
    required_courses: Mapped[int | None] = mapped_column(Integer)
    required_projects: Mapped[int | None] = mapped_column(Integer)


class StudentMilestone(Base):
    __tablename__ = "student_milestones"
    __table_args__ = (UniqueConstraint("student_id", "milestone_id", name="uq_student_milestone"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    milestone_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_milestones.id"))
    status: Mapped[MilestoneStatus] = mapped_column(pg_enum(MilestoneStatus, "milestone_status"), default=MilestoneStatus.not_started)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)


class Project(Base, Timestamps):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(pg_enum(ProjectStatus, "project_status"), default=ProjectStatus.not_started)
    start_date: Mapped[date | None] = mapped_column(Date)
    due_date: Mapped[date | None] = mapped_column(Date)
    completion_date: Mapped[date | None] = mapped_column(Date)
    grade: Mapped[str | None] = mapped_column(String(4))
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


# ---------- Risk ----------

class RiskRule(Base, Timestamps):
    __tablename__ = "risk_rules"
    id: Mapped[uuid.UUID] = UUID_PK()
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    academic_level: Mapped[AcademicLevel | None] = mapped_column(pg_enum(AcademicLevel, "academic_level"))
    indicator_type: Mapped[RiskIndicatorType] = mapped_column(pg_enum(RiskIndicatorType, "risk_indicator_type"))
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    severity: Mapped[Severity] = mapped_column(pg_enum(Severity, "severity"))
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[RiskLevel] = mapped_column(pg_enum(RiskLevel, "risk_level"), index=True)
    assessment_date: Mapped[datetime] = mapped_column(TZ, default=now_tz, index=True)
    assessment_version: Mapped[str] = mapped_column(String(16), default="v1")
    summary: Mapped[str | None] = mapped_column(Text)
    data_completeness_note: Mapped[str | None] = mapped_column(Text)

    factors: Mapped[list["RiskFactor"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class RiskFactor(Base):
    __tablename__ = "risk_factors"
    id: Mapped[uuid.UUID] = UUID_PK()
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_assessments.id"), index=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("risk_rules.id"))
    factor_name: Mapped[str] = mapped_column(String(255))
    observed_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    severity: Mapped[Severity] = mapped_column(pg_enum(Severity, "severity"))
    explanation: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    points_contributed: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))

    assessment: Mapped[RiskAssessment] = relationship(back_populates="factors")


# ---------- Interventions ----------

class Intervention(Base, Timestamps):
    __tablename__ = "interventions"
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    staff_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    intervention_type: Mapped[InterventionType] = mapped_column(pg_enum(InterventionType, "intervention_type"))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[InterventionStatus] = mapped_column(pg_enum(InterventionStatus, "intervention_status"), default=InterventionStatus.open)
    outcome: Mapped[InterventionOutcome | None] = mapped_column(pg_enum(InterventionOutcome, "intervention_outcome"))
    follow_up_date: Mapped[date | None] = mapped_column(Date, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    detail: Mapped["InterventionDetail | None"] = relationship(back_populates="intervention", uselist=False, cascade="all, delete-orphan")


class InterventionHistory(Base):
    __tablename__ = "intervention_history"
    id: Mapped[uuid.UUID] = UUID_PK()
    intervention_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interventions.id"), index=True)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=now_naive)
    field_changed: Mapped[str] = mapped_column(Text)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)


# ---------- Notifications ----------

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = UUID_PK()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    student_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("students.id"))
    notification_type: Mapped[NotificationType] = mapped_column(pg_enum(NotificationType, "notification_type"))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(pg_enum(Severity, "severity"), default=Severity.info)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    dedupe_key: Mapped[str | None] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(TZ, default=now_tz, index=True)

    deliveries: Mapped[list["NotificationDelivery"]] = relationship(cascade="all, delete-orphan")


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    id: Mapped[uuid.UUID] = UUID_PK()
    notification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("notifications.id"), index=True)
    channel: Mapped[DeliveryChannel] = mapped_column(pg_enum(DeliveryChannel, "delivery_channel"))
    delivery_status: Mapped[DeliveryStatus] = mapped_column(pg_enum(DeliveryStatus, "delivery_status"), default=DeliveryStatus.pending)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(TZ)
    error_message: Mapped[str | None] = mapped_column(Text)


# ---------- Administration ----------

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[uuid.UUID] = UUID_PK()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    before_data: Mapped[dict | list | None] = mapped_column(JSON)
    after_data: Mapped[dict | list | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_naive, index=True)


class DataImport(Base):
    __tablename__ = "data_imports"
    id: Mapped[uuid.UUID] = UUID_PK()
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String(255))
    import_type: Mapped[ImportType] = mapped_column(pg_enum(ImportType, "import_type"))
    status: Mapped[ImportStatus] = mapped_column(pg_enum(ImportStatus, "import_status"), default=ImportStatus.pending)
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    successful_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_naive)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    validated_rows: Mapped[dict | list | None] = mapped_column(JSON)
    row_errors: Mapped[dict | list | None] = mapped_column(JSON)


class PolicySetting(Base):
    __tablename__ = "policy_settings"
    id: Mapped[uuid.UUID] = UUID_PK()
    key: Mapped[str] = mapped_column(String(128), unique=True)
    value: Mapped[dict | list | str | int | float | bool] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_naive, onupdate=now_naive)


# =====================================================================
# Part 2: extension tables (not in the DBML diagram)
# =====================================================================

class StaffProfile(Base):
    """Job title, caseload capacity and (for instructors) the course they teach."""
    __tablename__ = "staff_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    capacity: Mapped[int | None] = mapped_column(Integer)
    course_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("courses.id"))

    user: Mapped[User] = relationship(back_populates="staff_profile")


class AssessmentScore(Base):
    """In-term scores: weekly assignments (week 1..12) and quiz/OPPE/end-term (week 0)."""
    __tablename__ = "assessment_scores"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "academic_term_id", "kind", "week", name="uq_assessment_score"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    academic_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id"))
    kind: Mapped[str] = mapped_column(String(16))  # assignment | quiz1 | quiz2 | oppe1 | oppe2 | endterm
    week: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    recorded_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)


class OppeExam(Base):
    __tablename__ = "oppe_exams"
    __table_args__ = (UniqueConstraint("course_id", "academic_term_id", "title", name="uq_oppe_exam"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    academic_term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_terms.id"))
    title: Mapped[str] = mapped_column(String(64))
    exam_date: Mapped[datetime] = mapped_column(TZ)


class OppeEligibility(Base):
    """One student's eligibility conditions for one OPPE, with their own values."""
    __tablename__ = "oppe_eligibility"
    __table_args__ = (UniqueConstraint("student_id", "oppe_exam_id", name="uq_oppe_eligibility"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    oppe_exam_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("oppe_exams.id"))
    criteria: Mapped[list] = mapped_column(JSON)
    if_not_eligible: Mapped[str | None] = mapped_column(Text)


class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[uuid.UUID] = UUID_PK()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    start_at: Mapped[datetime] = mapped_column(TZ, index=True)
    end_at: Mapped[datetime] = mapped_column(TZ)
    link: Mapped[str | None] = mapped_column(String(512))
    organizer: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)


class StudyPlanProgress(Base):
    """A ticked task in a student's study plan. task_key is "<week>-<task index>"."""
    __tablename__ = "study_plan_progress"
    __table_args__ = (UniqueConstraint("student_id", "course_id", "task_key", name="uq_study_plan_task"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    task_key: Mapped[str] = mapped_column(String(32))
    done_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)


class CourseContent(Base):
    """Per-course content shown to students: guide, study plan, insight, grading scheme."""
    __tablename__ = "course_content"
    __table_args__ = (UniqueConstraint("course_id", "kind", name="uq_course_content"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    course_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("courses.id"))
    kind: Mapped[str] = mapped_column(String(16))  # guide | plan | insight | scheme
    data: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(TZ, default=now_tz, onupdate=now_tz)


class InterventionDetail(Base):
    """What the intervention was about, and the instructor's support plan if there is one."""
    __tablename__ = "intervention_details"
    intervention_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interventions.id"), primary_key=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("courses.id"))
    reason_key: Mapped[str | None] = mapped_column(String(64))
    referral_to_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    follow_up_at: Mapped[datetime | None] = mapped_column(TZ)
    support_plan: Mapped[dict | None] = mapped_column(JSON)  # {status, link, reason, plan: [...]}

    intervention: Mapped[Intervention] = relationship(back_populates="detail")


class SharedSuggestion(Base):
    """A suggested action that staff marked as shared with the student."""
    __tablename__ = "shared_suggestions"
    __table_args__ = (UniqueConstraint("student_id", "action_key", name="uq_shared_suggestion"),)
    id: Mapped[uuid.UUID] = UUID_PK()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"), index=True)
    action_key: Mapped[str] = mapped_column(String(128))
    shared_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)


class RuleVersion(Base):
    """History of the risk and milestone rules; the highest version is in force."""
    __tablename__ = "rule_versions"
    id: Mapped[uuid.UUID] = UUID_PK()
    version: Mapped[int] = mapped_column(Integer, unique=True)
    effective: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(TZ, default=now_tz)


class SystemJob(Base):
    """Background work shown on the Data and system page."""
    __tablename__ = "system_jobs"
    id: Mapped[uuid.UUID] = UUID_PK()
    name: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | running | succeeded | failed
    run_at: Mapped[datetime] = mapped_column(TZ, default=now_tz, index=True)
