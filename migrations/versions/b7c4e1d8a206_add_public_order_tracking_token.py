
"""Add secure public tracking tokens to B2B orders.

Revision ID: b7c4e1d8a206
Revises: a6d9c2e51f80
"""

import secrets

from alembic import op
import sqlalchemy as sa


revision = "b7c4e1d8a206"
down_revision = "a6d9c2e51f80"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "tracking_token",
            sa.String(length=64),
            nullable=True,
        ),
    )

    # Los pedidos existentes también reciben un token aleatorio.
    # No se derivan tokens a partir del ID secuencial del pedido.
    bind = op.get_bind()

    orders_table = sa.table(
        "orders",
        sa.column("id", sa.Integer()),
        sa.column("tracking_token", sa.String(length=64)),
    )

    rows = bind.execute(
        sa.select(orders_table.c.id).where(
            orders_table.c.tracking_token.is_(None)
        )
    ).fetchall()

    for row in rows:
        bind.execute(
            sa.update(orders_table)
            .where(orders_table.c.id == row[0])
            .values(
                tracking_token=secrets.token_urlsafe(32)
            )
        )

    op.create_index(
        "uq_orders_tracking_token",
        "orders",
        ["tracking_token"],
        unique=True,
        mssql_where=sa.text(
            "tracking_token IS NOT NULL"
        ),
        postgresql_where=sa.text(
            "tracking_token IS NOT NULL"
        ),
        sqlite_where=sa.text(
            "tracking_token IS NOT NULL"
        ),
    )


def downgrade():
    op.drop_index(
        "uq_orders_tracking_token",
        table_name="orders",
    )

    op.drop_column(
        "orders",
        "tracking_token",
    )
