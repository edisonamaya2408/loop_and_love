from dataclasses import dataclass
from datetime import datetime


@dataclass
class AdminUserEntity:
    """Entidad de dominio de un usuario administrativo."""

    id: int | None
    email: str
    password_hash: str
    is_active: bool
    token_version: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None