from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)


class AdminAuditRepository(ABC):
    """Contrato de persistencia para eventos de auditoría."""

    @abstractmethod
    def record(
        self,
        event: AdminAuditEventEntity,
    ) -> AdminAuditEventEntity:
        """Agrega un evento nuevo sin exponer operaciones de edición."""
        raise NotImplementedError

    @abstractmethod
    def list_paginated(
        self,
        *,
        actor: str | None,
        action: str | None,
        entity_type: str | None,
        entity_id: str | None,
        date_from: datetime | None,
        date_to_exclusive: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[list[AdminAuditEventEntity], int]:
        """Consulta eventos con filtros y paginación."""
        raise NotImplementedError