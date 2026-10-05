from datetime import datetime, timezone

from app.extensions import db
from app.infrastructure.database.types import UTCDateTime
from app.infrastructure.database.models.order_status_history_model import (
    OrderStatusHistory,
)


class Order(db.Model):
    """Modelo de persistencia de pedidos B2B."""

    __tablename__ = "orders"

    __table_args__ = (
        db.Index(
            "ix_orders_created_at",
            "created_at",
        ),
        db.Index(
            "ix_orders_status",
            "status",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    customer_name = db.Column(
        db.Unicode(150),
        nullable=False,
    )

    phone = db.Column(
        db.Unicode(30),
        nullable=False,
    )

    city = db.Column(
        db.Unicode(100),
        nullable=False,
    )

    address = db.Column(
        db.Unicode(200),
        nullable=True,
    )

    observations = db.Column(
        db.UnicodeText,
        nullable=True,
    )

    status = db.Column(
        db.Unicode(20),
        nullable=False,
        default="pending",
    )

    total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
    )

    created_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    items = db.relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
        passive_deletes=True,
    )

    status_history = db.relationship(
        OrderStatusHistory,
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by=(
            OrderStatusHistory.changed_at,
            OrderStatusHistory.id,
        ),
    )

    def __repr__(self):
        return (
            f"<Order {self.id}: "
            f"{self.customer_name} - "
            f"{self.status}>"
        )


class OrderItem(db.Model):
    """Modelo de persistencia para las líneas de pedido."""

    __tablename__ = "order_items"

    __table_args__ = (
        db.Index(
            "ix_order_items_order_id",
            "order_id",
        ),
        db.Index(
            "ix_order_items_product_id",
            "product_id",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "orders.id",
            name="fk_order_items_order_id_orders",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            name="fk_order_items_product_id_products",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    product_code = db.Column(
        db.Unicode(50),
        nullable=False,
    )

    product_name = db.Column(
        db.Unicode(150),
        nullable=False,
    )

    unit_price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
    )

    line_total = db.Column(
        db.Numeric(14, 2),
        nullable=False,
    )

    order = db.relationship(
        "Order",
        back_populates="items",
    )

    def __repr__(self):
        return (
            f"<OrderItem {self.id}: "
            f"order={self.order_id} "
            f"product={self.product_id}>"
        )