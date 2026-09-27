from dataclasses import dataclass
from datetime import datetime


@dataclass
class CategoryEntity:
    """Entidad de dominio de una categoría de productos."""

    id: int | None
    name: str
    slug: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None