from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderStatusHistoryEntity:
    """Registro inmutable de un cambio de estado de pedido."""

    id: int | None
    order_id: int
    previous_status: str | None
    new_status: str
    changed_at: datetime | None