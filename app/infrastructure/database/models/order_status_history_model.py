from datetime import datetime, timezone

from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class OrderStatusHistory(db.Model):
    """Modelo de persistencia del historial de estados de pedidos."""

    __tablename__ = "order_status_history"

    __table_args__ = (
        db.Index(
            "ix_order_status_history_order_changed_at",
            "order_id",
            "changed_at",
        ),
        db.CheckConstraint(
            """
            previous_status IS NULL
            OR previous_status IN (
                'pending',
                'confirmed',
                'cancelled'
            )
            """,
            name="ck_order_status_history_previous_status",
        ),
        db.CheckConstraint(
            """
            new_status IN (
                'pending',
                'confirmed',
                'cancelled'
            )
            """,
            name="ck_order_status_history_new_status",
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
            name="fk_order_status_history_order_id_orders",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    previous_status = db.Column(
        db.Unicode(20),
        nullable=True,
    )

    new_status = db.Column(
        db.Unicode(20),
        nullable=False,
    )

    changed_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    order = db.relationship(
        "Order",
        back_populates="status_history",
    )

    def __repr__(self):
        return (
            f"<OrderStatusHistory "
            f"{self.id}: "
            f"order={self.order_id} "
            f"{self.previous_status} "
            f"-> "
            f"{self.new_status}>"
        )