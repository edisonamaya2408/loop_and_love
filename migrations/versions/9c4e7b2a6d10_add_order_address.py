"""add address to orders

Revision ID: 9c4e7b2a6d10
Revises: 8a5b9c7d1e20
Create Date: 2026-09-30 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "9c4e7b2a6d10"
down_revision = "8a5b9c7d1e20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "address",
            sa.Unicode(
                length=200
            ),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "orders",
        "address",
    )