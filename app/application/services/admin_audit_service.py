import json
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.application.dto.paginated_result import (
    PaginatedResult,
    PaginationMetadata,
)
from app.application.dto.pagination import (
    PaginationParams,
)
from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)
from app.domain.repositories.admin_audit_repository import (
    AdminAuditRepository,
)


class AdminAuditService:
    """Validación y coordinación de eventos y consultas de auditoría."""

    MAX_DETAILS_CHARACTERS = 16000
    MAX_ACTOR_FILTER_LENGTH = 120
    MAX_ENTITY_ID_LENGTH = 64
    BUSINESS_TIMEZONE = ZoneInfo("America/Bogota")

    ALLOWED_ENTITY_TYPES = frozenset({
        "product",
        "category",
        "order",
        "admin_user",
    })

    ALLOWED_ACTIONS = frozenset({
        "product.created",
        "product.updated",
        "product.activated",
        "product.deactivated",
        "product.status_changed",
        "product.image_deleted",
        "product.deleted",
        "category.created",
        "category.updated",
        "category.deleted",
        "admin_user.created",
        "admin_user.updated",
        "admin_user.activated",
        "admin_user.deactivated",
        "order.confirmed",
        "order.cancelled",
        "order.status_changed",
    })

    def __init__(
        self,
        repository: AdminAuditRepository,
    ):
        self.repository = repository

    def record(
        self,
        event: AdminAuditEventEntity,
    ) -> AdminAuditEventEntity:
        if not event.action or len(event.action) > 80:
            raise ValueError(
                "La acción de auditoría no es válida."
            )

        if not event.entity_type or len(event.entity_type) > 40:
            raise ValueError(
                "El tipo de entidad de auditoría no es válido."
            )

        if not event.actor_name.strip():
            raise ValueError(
                "El nombre del actor es obligatorio."
            )

        if not event.actor_email.strip():
            raise ValueError(
                "El correo del actor es obligatorio."
            )

        if not isinstance(event.details, dict):
            raise ValueError(
                "Los detalles de auditoría deben ser un objeto."
            )

        serialized = json.dumps(
            event.details,
            ensure_ascii=False,
            default=str,
        )

        if len(serialized) > self.MAX_DETAILS_CHARACTERS:
            event = replace(
                event,
                details={
                    "truncated": True,
                    "available_fields": list(
                        event.details.keys()
                    )[:100],
                },
            )

        return self.repository.record(event)

    @staticmethod
    def _optional_text(
        value,
        parameter_name: str,
        max_length: int,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                f"El filtro {parameter_name} debe ser texto."
            )

        value = value.strip()

        if not value:
            return None

        if len(value) > max_length:
            raise ValueError(
                f"El filtro {parameter_name} no puede superar "
                f"{max_length} caracteres."
            )

        return value

    @classmethod
    def _parse_local_date(
        cls,
        value,
        parameter_name: str,
    ) -> date | None:
        value = cls._optional_text(
            value,
            parameter_name,
            10,
        )

        if value is None:
            return None

        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"El filtro {parameter_name} debe usar "
                "el formato AAAA-MM-DD."
            ) from exc

        if parsed.isoformat() != value:
            raise ValueError(
                f"El filtro {parameter_name} debe usar "
                "el formato AAAA-MM-DD."
            )

        return parsed

    @classmethod
    def _local_midnight_utc(
        cls,
        day: date,
    ) -> datetime:
        local_midnight = datetime.combine(
            day,
            time.min,
            tzinfo=cls.BUSINESS_TIMEZONE,
        )

        return local_midnight.astimezone(
            timezone.utc
        )

    def list_events(
        self,
        *,
        actor=None,
        action=None,
        entity_type=None,
        entity_id=None,
        date_from=None,
        date_to=None,
        page=None,
        per_page=None,
    ) -> PaginatedResult[AdminAuditEventEntity]:
        actor_filter = self._optional_text(
            actor,
            "actor",
            self.MAX_ACTOR_FILTER_LENGTH,
        )

        action_filter = self._optional_text(
            action,
            "action",
            80,
        )

        if (
            action_filter is not None
            and action_filter not in self.ALLOWED_ACTIONS
        ):
            raise ValueError(
                "El filtro action no corresponde "
                "a una operación válida."
            )

        entity_filter = self._optional_text(
            entity_type,
            "entity_type",
            40,
        )

        if (
            entity_filter is not None
            and entity_filter not in self.ALLOWED_ENTITY_TYPES
        ):
            raise ValueError(
                "El filtro entity_type no corresponde "
                "a una entidad válida."
            )

        entity_id_filter = self._optional_text(
            entity_id,
            "entity_id",
            self.MAX_ENTITY_ID_LENGTH,
        )

        from_day = self._parse_local_date(
            date_from,
            "date_from",
        )

        to_day = self._parse_local_date(
            date_to,
            "date_to",
        )

        if (
            from_day is not None
            and to_day is not None
            and from_day > to_day
        ):
            raise ValueError(
                "La fecha desde no puede ser posterior "
                "a la fecha hasta."
            )

        start_utc = (
            self._local_midnight_utc(from_day)
            if from_day is not None
            else None
        )

        # Fecha hasta inclusive: se compara con la medianoche
        # del día siguiente mediante un límite superior exclusivo.
        end_exclusive_utc = (
            self._local_midnight_utc(
                to_day + timedelta(days=1)
            )
            if to_day is not None
            else None
        )

        pagination_params = PaginationParams.from_values(
            page=page,
            per_page=(
                25 if per_page is None else per_page
            ),
        )

        items, total = self.repository.list_paginated(
            actor=actor_filter,
            action=action_filter,
            entity_type=entity_filter,
            entity_id=entity_id_filter,
            date_from=start_utc,
            date_to_exclusive=end_exclusive_utc,
            offset=pagination_params.offset,
            limit=pagination_params.per_page,
        )

        return PaginatedResult(
            items=items,
            pagination=PaginationMetadata(
                page=pagination_params.page,
                per_page=pagination_params.per_page,
                total=total,
            ),
        )