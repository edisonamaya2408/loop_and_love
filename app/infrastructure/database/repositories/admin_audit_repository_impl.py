import json
from datetime import datetime, timezone

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)
from app.domain.repositories.admin_audit_repository import (
    AdminAuditRepository,
)
from app.extensions import db
from app.infrastructure.database.models.admin_audit_log_model import (
    AdminAuditLog,
)


class SQLAlchemyAdminAuditRepository(AdminAuditRepository):
    """Persistencia SQLAlchemy para eventos de auditoría."""

    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(
        model: AdminAuditLog,
    ) -> AdminAuditEventEntity:
        try:
            details = json.loads(model.details_json)
        except (TypeError, ValueError):
            details = {}

        if not isinstance(details, dict):
            details = {}

        return AdminAuditEventEntity(
            id=model.id,
            actor_id=model.actor_id,
            actor_name=model.actor_name,
            actor_email=model.actor_email,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            details=details,
            ip_address=model.ip_address,
            request_id=model.request_id,
            created_at=model.created_at,
        )

    def record(
        self,
        event: AdminAuditEventEntity,
    ) -> AdminAuditEventEntity:
        model = AdminAuditLog(
            actor_id=event.actor_id,
            actor_name=event.actor_name,
            actor_email=event.actor_email,
            action=event.action,
            entity_type=event.entity_type,
            entity_id=(
                str(event.entity_id)
                if event.entity_id is not None
                else None
            ),
            details_json=json.dumps(
                event.details or {},
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            ),
            ip_address=event.ip_address,
            request_id=event.request_id,
            created_at=(
                event.created_at
                or datetime.now(timezone.utc)
            ),
        )

        try:
            self.session.add(model)
            self.session.flush()
            self.session.commit()
            self.session.refresh(model)
        except Exception:
            self.session.rollback()
            raise

        return self._to_entity(model)

    def list_paginated(
        self,
        *,
        actor: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        date_from: datetime | None = None,
        date_to_exclusive: datetime | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> tuple[list[AdminAuditEventEntity], int]:
        query = self.session.query(
            AdminAuditLog
        )

        if actor:
            escaped_actor = (
                actor.replace("/", "//")
                .replace("%", "/%")
                .replace("_", "/_")
            )

            pattern = f"%{escaped_actor}%"

            query = query.filter(
                or_(
                    AdminAuditLog.actor_name.ilike(
                        pattern,
                        escape="/",
                    ),
                    AdminAuditLog.actor_email.ilike(
                        pattern,
                        escape="/",
                    ),
                )
            )

        if action:
            query = query.filter(
                AdminAuditLog.action == action
            )

        if entity_type:
            query = query.filter(
                AdminAuditLog.entity_type == entity_type
            )

        if entity_id:
            query = query.filter(
                AdminAuditLog.entity_id == entity_id
            )

        if date_from is not None:
            query = query.filter(
                AdminAuditLog.created_at >= date_from
            )

        if date_to_exclusive is not None:
            query = query.filter(
                AdminAuditLog.created_at < date_to_exclusive
            )

        total = query.count()

        models = (
            query.order_by(
                desc(AdminAuditLog.created_at),
                desc(AdminAuditLog.id),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [
            self._to_entity(model)
            for model in models
        ], total