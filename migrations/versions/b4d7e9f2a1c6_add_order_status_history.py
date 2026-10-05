"""add order status history

Revision ID: b4d7e9f2a1c6
Revises: 9c4e7b2a6d10
Create Date: 2026-10-05 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "b4d7e9f2a1c6"
down_revision = "9c4e7b2a6d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "order_status_history",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "order_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "previous_status",
            sa.Unicode(
                length=20
            ),
            nullable=True,
        ),

        sa.Column(
            "new_status",
            sa.Unicode(
                length=20
            ),
            nullable=False,
        ),

        sa.Column(
            "changed_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),

        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=(
                "fk_order_status_history_order_id_orders"
            ),
            ondelete="CASCADE",
        ),

        sa.CheckConstraint(
            """
            previous_status IS NULL
            OR previous_status IN (
                'pending',
                'confirmed',
                'cancelled'
            )
            """,
            name=(
                "ck_order_status_history_previous_status"
            ),
        ),

        sa.CheckConstraint(
            """
            new_status IN (
                'pending',
                'confirmed',
                'cancelled'
            )
            """,
            name=(
                "ck_order_status_history_new_status"
            ),
        ),
    )


    op.create_index(
        "ix_order_status_history_order_changed_at",
        "order_status_history",
        [
            "order_id",
            "changed_at",
        ],
        unique=False,
    )


    # Los pedidos existentes reciben un registro
    # inicial utilizando su fecha de creación.
    op.execute(
        sa.text(
            """
            INSERT INTO order_status_history (
                order_id,
                previous_status,
                new_status,
                changed_at
            )
            SELECT
                id,
                NULL,
                status,
                created_at
            FROM orders
            """
        )
    )


def downgrade():

    op.drop_index(
        "ix_order_status_history_order_changed_at",
        table_name="order_status_history",
    )

    op.drop_table(
        "order_status_history"
    )