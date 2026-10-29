"""Persist delivery quote snapshots on orders.

Revision ID: e4f8c9b2d710
Revises: d3c4e1a8f205
"""

from alembic import op
import sqlalchemy as sa


revision = "e4f8c9b2d710"
down_revision = "d3c4e1a8f205"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "orders",
        sa.Column(
            "delivery_fee",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_latitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_longitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_straight_distance_km",
            sa.Numeric(8, 2),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_distance_km",
            sa.Numeric(8, 2),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_billable_km",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_base_fee",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_price_per_km",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "delivery_distance_factor",
            sa.Numeric(5, 2),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_orders_delivery_fee_nonnegative",
        "orders",
        "delivery_fee >= 0",
    )

    op.create_check_constraint(
        "ck_orders_delivery_coordinates_pair",
        "orders",
        """
        (delivery_latitude IS NULL
         AND delivery_longitude IS NULL)
        OR
        (delivery_latitude IS NOT NULL
         AND delivery_longitude IS NOT NULL)
        """,
    )


def downgrade():
    op.drop_constraint(
        "ck_orders_delivery_coordinates_pair",
        "orders",
        type_="check",
    )

    op.drop_constraint(
        "ck_orders_delivery_fee_nonnegative",
        "orders",
        type_="check",
    )

    op.drop_column("orders", "delivery_distance_factor")
    op.drop_column("orders", "delivery_price_per_km")
    op.drop_column("orders", "delivery_base_fee")
    op.drop_column("orders", "delivery_billable_km")
    op.drop_column("orders", "delivery_distance_km")
    op.drop_column("orders", "delivery_straight_distance_km")
    op.drop_column("orders", "delivery_longitude")
    op.drop_column("orders", "delivery_latitude")
    op.drop_column("orders", "delivery_fee")