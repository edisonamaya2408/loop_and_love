
"""Add idempotency support to public B2B orders.

Revision ID: a6d9c2e51f80
Revises: e23b7a9c51d4
"""

from alembic import op
import sqlalchemy as sa


revision = "a6d9c2e51f80"
down_revision = "e23b7a9c51d4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "idempotency_key",
            sa.String(length=36),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "request_fingerprint",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.create_index(
        "uq_orders_idempotency_key",
        "orders",
        ["idempotency_key"],
        unique=True,
        mssql_where=sa.text(
            "idempotency_key IS NOT NULL"
        ),
        postgresql_where=sa.text(
            "idempotency_key IS NOT NULL"
        ),
    )


def downgrade():
    op.drop_index(
        "uq_orders_idempotency_key",
        table_name="orders",
    )

    op.drop_column(
        "orders",
        "request_fingerprint",
    )

    op.drop_column(
        "orders",
        "idempotency_key",
    )