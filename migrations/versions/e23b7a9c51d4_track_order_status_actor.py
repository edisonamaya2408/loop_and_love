
"""Track the administrator responsible for order status changes.

Revision ID: e23b7a9c51d4
Revises: f2a9c6d31b70
"""

from alembic import op
import sqlalchemy as sa


revision = "e23b7a9c51d4"
down_revision = "f2a9c6d31b70"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "order_status_history",
        sa.Column(
            "changed_by_admin_user_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "order_status_history",
        sa.Column(
            "changed_by_name",
            sa.Unicode(length=120),
            nullable=True,
        ),
    )

    op.add_column(
        "order_status_history",
        sa.Column(
            "changed_by_email",
            sa.Unicode(length=255),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_order_status_history_changed_by_admin_user_id_admin_users",
        "order_status_history",
        "admin_users",
        ["changed_by_admin_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint(
        "fk_order_status_history_changed_by_admin_user_id_admin_users",
        "order_status_history",
        type_="foreignkey",
    )

    op.drop_column(
        "order_status_history",
        "changed_by_email",
    )

    op.drop_column(
        "order_status_history",
        "changed_by_name",
    )

    op.drop_column(
        "order_status_history",
        "changed_by_admin_user_id",
    )
