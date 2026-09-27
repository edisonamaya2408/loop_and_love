from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class ProductResponse:
    """DTO de lectura utilizado por la API de productos."""

    id: int | None
    code: str
    name: str
    description: str | None
    price: Decimal
    category_id: int
    category_name: str | None
    category_slug: str | None
    image_url: str | None
    is_active: bool
    created_at: datetime | None
    updated_at: datetime | None