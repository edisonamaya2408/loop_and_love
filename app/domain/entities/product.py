from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class ProductEntity:
    """Entidad de dominio de un producto."""

    id: int | None
    code: str
    name: str
    description: str | None
    price: Decimal
    category_id: int
    image_url: str | None
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None