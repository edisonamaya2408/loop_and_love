from flask import Blueprint, current_app, jsonify, request

from app.application.services.admin_audit_service import (
    AdminAuditService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyAdminAuditRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)


admin_audit_bp = Blueprint(
    "admin_audit",
    __name__,
    url_prefix="/api/admin/audit-logs",
)


def _get_admin_audit_service() -> AdminAuditService:
    repository = current_app.extensions.get(
        "admin_audit_repository"
    )

    if repository is None:
        repository = SQLAlchemyAdminAuditRepository()

    return AdminAuditService(repository)


def _audit_event_to_dict(event):
    return {
        "id": event.id,
        "actor_id": event.actor_id,
        "actor_name": event.actor_name,
        "actor_email": event.actor_email,
        "action": event.action,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "details": event.details,
        "ip_address": event.ip_address,
        "request_id": event.request_id,
        "created_at": (
            event.created_at.isoformat()
            if event.created_at
            else None
        ),
    }


@admin_audit_bp.get("")
@jwt_required
def list_admin_audit_logs():
    """Consulta eventos de auditoría con filtros y paginación."""

    try:
        result = _get_admin_audit_service().list_events(
            actor=request.args.get("actor"),
            action=request.args.get("action"),
            entity_type=request.args.get("entity_type"),
            entity_id=request.args.get("entity_id"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            page=request.args.get("page"),
            per_page=request.args.get("per_page"),
        )
    except ValueError as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_AUDIT_FILTERS",
                    "message": str(exc),
                },
            }
        ), 400

    pagination = result.pagination

    return jsonify(
        {
            "success": True,
            "data": [
                _audit_event_to_dict(event)
                for event in result.items
            ],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_previous": pagination.has_previous,
            },
        }
    ), 200