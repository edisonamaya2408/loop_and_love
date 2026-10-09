"""add admin audit logs

Revision ID: f2a9c6d31b70
Revises: c7e4a2f918d0
"""

from alembic import op
import sqlalchemy as sa


revision = "f2a9c6d31b70"
down_revision = "c7e4a2f918d0"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_audit_logs",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "actor_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "actor_name",
            sa.Unicode(length=120),
            nullable=False,
        ),

        sa.Column(
            "actor_email",
            sa.Unicode(length=255),
            nullable=False,
        ),

        sa.Column(
            "action",
            sa.Unicode(length=80),
            nullable=False,
        ),

        sa.Column(
            "entity_type",
            sa.Unicode(length=40),
            nullable=False,
        ),

        sa.Column(
            "entity_id",
            sa.Unicode(length=64),
            nullable=True,
        ),

        sa.Column(
            "details_json",
            sa.UnicodeText(),
            nullable=False,
        ),

        sa.Column(
            "ip_address",
            sa.Unicode(length=45),
            nullable=True,
        ),

        sa.Column(
            "request_id",
            sa.Unicode(length=64),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["admin_users.id"],
            name=(
                "fk_admin_audit_logs_actor_id_admin_users"
            ),
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_admin_audit_logs_created_at",
        "admin_audit_logs",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_admin_audit_logs_actor_created_at",
        "admin_audit_logs",
        [
            "actor_id",
            "created_at",
        ],
        unique=False,
    )

    op.create_index(
        "ix_admin_audit_logs_entity_created_at",
        "admin_audit_logs",
        [
            "entity_type",
            "entity_id",
            "created_at",
        ],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_admin_audit_logs_entity_created_at",
        table_name="admin_audit_logs",
    )

    op.drop_index(
        "ix_admin_audit_logs_actor_created_at",
        table_name="admin_audit_logs",
    )

    op.drop_index(
        "ix_admin_audit_logs_created_at",
        table_name="admin_audit_logs",
    )

    op.drop_table(
        "admin_audit_logs"
    )