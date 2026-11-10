"""Fast lookups and compact storage

- HASH indexes for columns only ever compared with "=" (UUID foreign keys, audit
  action/entity, notification dedupe key, lower(email) for sign-in). A hash index
  keeps a 4-byte hash per row instead of the full key, so it is smaller than a
  B-tree on wide keys and answers equality in one bucket probe.
- Composite B-trees where a query filters on one column and sorts or ranges on
  another (meetings, notifications, risk history).
- Drops indexes that only repeated the first column of a unique constraint, and
  indexes on columns with a handful of values (role, risk level, flags).
- lz4 TOAST compression for JSON and long text columns.
- data_version: a one-row change counter used for ETags (304 Not Modified).
- risk_snapshots: weekly counts per risk level for the Overview trend.

Revision ID: a7c4e2f91b30
Revises: 0425728f46cd
Create Date: 2026-11-10 17:09:53.330416
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = 'a7c4e2f91b30'
down_revision = '0425728f46cd'
branch_labels = None
depends_on = None

# Redundant (covered by a unique constraint's leading column) or low-selectivity.
DROPPED = [
    ('assessment_scores', 'ix_assessment_scores_student_id', ['student_id']),
    ('course_results', 'ix_course_results_student_id', ['student_id']),
    ('oppe_eligibility', 'ix_oppe_eligibility_student_id', ['student_id']),
    ('registrations', 'ix_registrations_student_id', ['student_id']),
    ('shared_suggestions', 'ix_shared_suggestions_student_id', ['student_id']),
    ('student_milestones', 'ix_student_milestones_student_id', ['student_id']),
    ('study_plan_progress', 'ix_study_plan_progress_student_id', ['student_id']),
    ('audit_logs', 'ix_audit_logs_entity_type', ['entity_type']),
    ('student_assignments', 'ix_student_assignments_is_active', ['is_active']),
    ('students', 'ix_students_academic_level', ['academic_level']),
    ('users', 'ix_users_role', ['role']),
    ('notifications', 'ix_notifications_is_read', ['is_read']),
]
# Replaced by a composite B-tree.
REPLACED = [
    ('meetings', 'ix_meetings_user_id', ['user_id']),
    ('meetings', 'ix_meetings_start_at', ['start_at']),
    ('notifications', 'ix_notifications_user_id', ['user_id']),
    ('notifications', 'ix_notifications_created_at', ['created_at']),
    ('risk_assessments', 'ix_risk_assessments_student_id', ['student_id']),
    ('risk_assessments', 'ix_risk_assessments_risk_level', ['risk_level']),
    ('risk_assessments', 'ix_risk_assessments_assessment_date', ['assessment_date']),
]
COMPOSITE = [
    ('meetings', 'ix_meetings_user_end', ['user_id', 'end_at']),
    ('notifications', 'ix_notifications_user_created', ['user_id', 'created_at']),
    ('risk_assessments', 'ix_risk_assessments_student_date', ['student_id', 'assessment_date']),
]
# Same name, B-tree -> HASH (equality-only lookups).
TO_HASH = [
    ('students', 'ix_students_assigned_staff', 'assigned_staff_id'),
    ('student_assignments', 'ix_student_assignments_student_id', 'student_id'),
    ('student_assignments', 'ix_student_assignments_staff_user_id', 'staff_user_id'),
    ('registration_validation_logs', 'ix_registration_validation_logs_student_id', 'student_id'),
    ('projects', 'ix_projects_student_id', 'student_id'),
    ('risk_factors', 'ix_risk_factors_assessment_id', 'assessment_id'),
    ('interventions', 'ix_interventions_student_id', 'student_id'),
    ('intervention_history', 'ix_intervention_history_intervention_id', 'intervention_id'),
    ('notifications', 'ix_notifications_dedupe_key', 'dedupe_key'),
    ('notification_deliveries', 'ix_notification_deliveries_notification_id', 'notification_id'),
    ('audit_logs', 'ix_audit_logs_action', 'action'),
    ('audit_logs', 'ix_audit_logs_entity_id', 'entity_id'),
]
# JSON and long-text columns that benefit from lz4 TOAST compression.
COMPRESSED = [
    ('audit_logs', 'before_data'), ('audit_logs', 'after_data'),
    ('data_imports', 'validated_rows'), ('data_imports', 'row_errors'),
    ('course_content', 'data'), ('policy_settings', 'value'), ('rule_versions', 'snapshot'),
    ('intervention_details', 'support_plan'), ('oppe_eligibility', 'criteria'),
    ('registration_validation_logs', 'requested_courses'), ('registration_validation_logs', 'validation_result'),
    ('interventions', 'description'), ('risk_assessments', 'summary'), ('risk_factors', 'explanation'),
]


def _lz4_available() -> bool:
    return bool(op.get_bind().execute(sa.text(
        "select 1 from pg_settings where name = 'default_toast_compression' and 'lz4' = any(enumvals)")).scalar())


def upgrade() -> None:
    op.create_table(
        'data_version',
        sa.Column('id', sa.SmallInteger(), nullable=False),
        sa.Column('version', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute("INSERT INTO data_version (id, version) VALUES (1, 1)")
    op.create_table(
        'risk_snapshots',
        sa.Column('term_id', sa.Uuid(), nullable=False),
        sa.Column('week', sa.SmallInteger(), nullable=False),
        sa.Column('level', postgresql.ENUM('low', 'moderate', 'high', 'critical', name='risk_level', create_type=False), nullable=False),
        sa.Column('students', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['term_id'], ['academic_terms.id']),
        sa.PrimaryKeyConstraint('term_id', 'week', 'level'),
    )

    for table, name, _ in DROPPED + REPLACED:
        op.drop_index(name, table_name=table)
    for table, name, cols in COMPOSITE:
        op.create_index(name, table, cols)
    for table, name, col in TO_HASH:
        op.drop_index(name, table_name=table)
        op.create_index(name, table, [col], postgresql_using='hash')
    op.create_index('ix_users_email_lower', 'users', [sa.literal_column('lower(email)')], postgresql_using='hash')

    if _lz4_available():
        for table, col in COMPRESSED:
            op.execute(f'ALTER TABLE {table} ALTER COLUMN {col} SET COMPRESSION lz4')


def downgrade() -> None:
    if _lz4_available():
        for table, col in COMPRESSED:
            op.execute(f'ALTER TABLE {table} ALTER COLUMN {col} SET COMPRESSION default')
    op.drop_index('ix_users_email_lower', table_name='users')
    for table, name, col in TO_HASH:
        op.drop_index(name, table_name=table)
        op.create_index(name, table, [col])
    for table, name, _ in COMPOSITE:
        op.drop_index(name, table_name=table)
    for table, name, cols in DROPPED + REPLACED:
        op.create_index(name, table, cols)
    op.drop_table('risk_snapshots')
    op.drop_table('data_version')
