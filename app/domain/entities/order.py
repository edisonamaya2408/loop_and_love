from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.domain.entities.order_status_history import (
    OrderStatusHistoryEntity,
)


ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_CONFIRMED = "confirmed"
ORDER_STATUS_CANCELLED = "cancelled"


@dataclass(frozen=True)
class OrderItemEntity:
    """Línea de pedido con snapshot de datos comerciales."""

    id: int | None
    product_id: int | None
    product_code: str
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


@dataclass
class OrderEntity:
    """Entidad de dominio de un pedido B2B."""

    id: int | None
    customer_name: str
    phone: str
    city: str
    address: str | None
    observations: str | None
    status: str
    total: Decimal
    items: list[OrderItemEntity] = field(
        default_factory=list
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None

    status_history: list[
        OrderStatusHistoryEntity
    ] = field(
        default_factory=list
    )