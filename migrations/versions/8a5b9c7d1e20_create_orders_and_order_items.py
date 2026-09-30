"""create orders and order items

Revision ID: 8a5b9c7d1e20
Revises: d7e4f8a21c63
Create Date: 2026-09-29 16:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8a5b9c7d1e20"
down_revision = "d7e4f8a21c63"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "customer_name",
            sa.Unicode(length=150),
            nullable=False,
        ),
        sa.Column(
            "phone",
            sa.Unicode(length=30),
            nullable=False,
        ),
        sa.Column(
            "city",
            sa.Unicode(length=100),
            nullable=False,
        ),
        sa.Column(
            "observations",
            sa.UnicodeText(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Unicode(length=20),
            nullable=False,
        ),
        sa.Column(
            "total",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_orders_created_at",
        "orders",
        ["created_at"],
        unique=False,
    )

    op.create_index(
        "ix_orders_status",
        "orders",
        ["status"],
        unique=False,
    )

    op.create_table(
        "order_items",
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
            "product_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "product_code",
            sa.Unicode(length=50),
            nullable=False,
        ),
        sa.Column(
            "product_name",
            sa.Unicode(length=150),
            nullable=False,
        ),
        sa.Column(
            "unit_price",
            sa.Numeric(
                precision=12,
                scale=2,
            ),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "line_total",
            sa.Numeric(
                precision=14,
                scale=2,
            ),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_order_items_order_id_orders",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_order_items_product_id_products",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
    )

    op.create_index(
        "ix_order_items_order_id",
        "order_items",
        ["order_id"],
        unique=False,
    )

    op.create_index(
        "ix_order_items_product_id",
        "order_items",
        ["product_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_order_items_product_id",
        table_name="order_items",
    )

    op.drop_index(
        "ix_order_items_order_id",
        table_name="order_items",
    )

    op.drop_table(
        "order_items"
    )

    op.drop_index(
        "ix_orders_status",
        table_name="orders",
    )

    op.drop_index(
        "ix_orders_created_at",
        table_name="orders",
    )

    op.drop_table(
        "orders"
    )