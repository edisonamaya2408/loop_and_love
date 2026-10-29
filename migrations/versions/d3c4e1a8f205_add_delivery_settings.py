"""Add configurable delivery settings.

Revision ID: d3c4e1a8f205
Revises: c8a1f4d6b203
"""

from alembic import op
import sqlalchemy as sa


revision = "d3c4e1a8f205"
down_revision = "c8a1f4d6b203"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "delivery_settings",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "origin_latitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
        sa.Column(
            "origin_longitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
        sa.Column(
            "public_map_center_latitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
        sa.Column(
            "public_map_center_longitude",
            sa.Numeric(10, 7),
            nullable=True,
        ),
        sa.Column(
            "base_fee",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "price_per_km",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "distance_factor",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("1.30"),
        ),
        sa.Column(
            "max_distance_km",
            sa.Numeric(8, 2),
            nullable=False,
            server_default=sa.text("50"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "id = 1",
            name="ck_delivery_settings_singleton_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("delivery_settings")