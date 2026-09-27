"""add token version for admin JWT revocation

Revision ID: d7e4f8a21c63
Revises: c31d5e8f2a77
Create Date: 2026-09-24 13:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e4f8a21c63"
down_revision = "c31d5e8f2a77"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "admin_users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.create_check_constraint(
        "ck_admin_users_token_version_non_negative",
        "admin_users",
        "token_version >= 0",
    )


def downgrade():
    op.drop_constraint(
        "ck_admin_users_token_version_non_negative",
        "admin_users",
        type_="check",
    )

    op.drop_column(
        "admin_users",
        "token_version",
    )