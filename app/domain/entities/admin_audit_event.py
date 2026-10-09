from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AdminAuditEventEntity:
    """Evento inmutable de auditoría administrativa."""

    id: int | None
    actor_id: int | None
    actor_name: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: str | None
    details: dict = field(default_factory=dict)
    ip_address: str | None = None
    request_id: str | None = None
    created_at: datetime | None = None