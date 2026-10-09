import logging

from flask import (
    Flask,
    current_app,
    g,
    request,
)

from app.application.services.admin_audit_service import (
    AdminAuditService,
)
from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)
from app.infrastructure.database.repositories.admin_audit_repository_impl import (
    SQLAlchemyAdminAuditRepository,
)


logger = logging.getLogger(__name__)


_SENSITIVE_KEY_PARTS = (
    "password",
    "token",
    "secret",
    "api_key",
)


def _safe_request_fields() -> dict:
    """Extrae campos de la petición sin guardar secretos."""

    if request.is_json:
        payload = request.get_json(
            silent=True
        )
    else:
        payload = request.form.to_dict(
            flat=True
        )

    if not isinstance(payload, dict):
        payload = {}

    fields = {}
    credentials_changed = False

    for key, value in payload.items():
        field_name = str(key)[:80]
        normalized_key = field_name.lower()

        if any(
            sensitive_part in normalized_key
            for sensitive_part in _SENSITIVE_KEY_PARTS
        ):
            if value not in (
                None,
                "",
                False,
            ):
                credentials_changed = True

            continue

        if isinstance(value, str):
            fields[field_name] = value[:600]

        elif (
            value is None
            or type(value) in (
                bool,
                int,
                float,
            )
        ):
            fields[field_name] = value

        elif isinstance(value, list):
            safe_items = []

            for item in value[:25]:
                if isinstance(item, str):
                    safe_items.append(
                        item[:200]
                    )

                elif (
                    item is None
                    or type(item) in (
                        bool,
                        int,
                        float,
                    )
                ):
                    safe_items.append(item)

            fields[field_name] = safe_items

    if credentials_changed:
        fields["credentials_changed"] = True

    if request.files:
        fields["file_attached"] = any(
            bool(upload.filename)
            for upload in request.files.values()
        )

    return fields


def _response_data(response):
    body = response.get_json(
        silent=True
    )

    if not isinstance(body, dict):
        return None, None

    data = body.get("data")

    return body, (
        data
        if isinstance(data, dict)
        else None
    )


def _response_summary(
    entity_type: str,
    data: dict | None,
) -> dict:
    """Conserva solamente datos útiles para la auditoría."""

    if not isinstance(data, dict):
        return {}

    allowed_by_type = {
        "product": {
            "id",
            "name",
            "code",
            "category_id",
            "price",
            "is_active",
        },
        "category": {
            "id",
            "name",
            "slug",
            "is_active",
        },
        "admin_user": {
            "id",
            "name",
            "email",
            "is_active",
        },
        "order": {
            "id",
            "status",
        },
    }

    allowed = allowed_by_type.get(
        entity_type,
        set(),
    )

    return {
        key: value
        for key, value in data.items()
        if (
            key in allowed
            and (
                value is None
                or isinstance(value, str)
                or type(value) in (
                    bool,
                    int,
                    float,
                )
            )
        )
    }


def _build_mutation_description(
    response,
) -> dict | None:
    """Clasifica una mutación administrativa exitosa."""

    if not (
        200 <= response.status_code < 300
    ):
        return None

    if request.method not in {
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }:
        return None

    parts = [
        part
        for part in request.path.strip("/").split("/")
        if part
    ]

    if (
        len(parts) < 3
        or parts[:2] != [
            "api",
            "admin",
        ]
    ):
        return None

    body, data = _response_data(
        response
    )

    if (
        isinstance(body, dict)
        and body.get("success") is False
    ):
        return None

    resource = parts[2]
    tail = parts[3:]

    fields = _safe_request_fields()

    action = None
    entity_type = None

    if resource == "products":
        entity_type = "product"

        if (
            request.method == "POST"
            and not tail
        ):
            action = "product.created"

        elif (
            request.method == "PUT"
            and len(tail) == 1
        ):
            action = "product.updated"

        elif (
            request.method == "PATCH"
            and len(tail) == 2
            and tail[1] == "status"
        ):
            active = (
                data.get("is_active")
                if data is not None
                else fields.get("is_active")
            )

            if isinstance(active, str):
                active = (
                    active.strip().lower()
                    in {
                        "true",
                        "1",
                        "yes",
                    }
                )

            if active is True:
                action = "product.activated"

            elif active is False:
                action = "product.deactivated"

            else:
                action = "product.status_changed"

        elif (
            request.method == "DELETE"
            and len(tail) == 2
            and tail[1] == "image"
        ):
            action = "product.image_deleted"

        elif (
            request.method == "DELETE"
            and len(tail) == 1
        ):
            action = "product.deleted"

    elif resource == "categories":
        entity_type = "category"

        if (
            request.method == "POST"
            and not tail
        ):
            action = "category.created"

        elif (
            request.method == "PUT"
            and len(tail) == 1
        ):
            action = "category.updated"

        elif (
            request.method == "DELETE"
            and len(tail) == 1
        ):
            action = "category.deleted"

    elif resource == "users":
        entity_type = "admin_user"

        if (
            request.method == "POST"
            and not tail
        ):
            action = "admin_user.created"

        elif (
            request.method == "PATCH"
            and len(tail) == 1
        ):
            active = fields.get(
                "is_active"
            )

            if active is False or (
                isinstance(active, str)
                and active.lower() == "false"
            ):
                action = "admin_user.deactivated"

            elif active is True or (
                isinstance(active, str)
                and active.lower() == "true"
            ):
                action = "admin_user.activated"

            else:
                action = "admin_user.updated"

    elif resource == "orders":
        entity_type = "order"

        if (
            request.method == "PATCH"
            and len(tail) == 2
            and tail[1] == "status"
        ):
            status = (
                data.get("status")
                if data is not None
                else fields.get("status")
            )

            if status == "confirmed":
                action = "order.confirmed"

            elif status == "cancelled":
                action = "order.cancelled"

            else:
                action = "order.status_changed"

    if action is None:
        return None

    entity_id = (
        tail[0]
        if tail and tail[0].isdigit()
        else (
            str(data["id"])
            if data is not None
            and data.get("id") is not None
            else None
        )
    )

    if entity_type == "order":
        history = (
            data.get("status_history", [])
            if data is not None
            else []
        )

        last_history = (
            history[-1]
            if isinstance(history, list)
            and history
            and isinstance(history[-1], dict)
            else {}
        )

        status = (
            data.get("status")
            if data is not None
            else fields.get("status")
        )

        details = {
            "previous_status": (
                last_history.get(
                    "previous_status"
                )
            ),
            "new_status": status,
        }

    else:
        details = {}

        if fields:
            details["fields"] = fields

        summary = _response_summary(
            entity_type,
            data,
        )

        if summary:
            details["result"] = summary

    return {
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details,
    }


def register_admin_audit(
    app: Flask,
) -> None:
    """Registra eventos de mutaciones administrativas exitosas."""

    @app.after_request
    def persist_admin_audit(response):
        actor = getattr(
            g,
            "authenticated_user",
            None,
        )

        if not isinstance(actor, dict):
            return response

        description = _build_mutation_description(
            response
        )

        if description is None:
            return response

        raw_actor_id = actor.get("id")

        actor_id = (
            raw_actor_id
            if (
                isinstance(raw_actor_id, int)
                and not isinstance(raw_actor_id, bool)
            )
            else None
        )

        event = AdminAuditEventEntity(
            id=None,
            actor_id=actor_id,
            actor_name=str(
                actor.get("name")
                or "Administrador"
            )[:120],
            actor_email=str(
                actor.get("email")
                or "desconocido"
            )[:255],
            action=description["action"],
            entity_type=description["entity_type"],
            entity_id=description["entity_id"],
            details=description["details"],
            ip_address=(
                request.remote_addr[:45]
                if request.remote_addr
                else None
            ),
            request_id=getattr(
                g,
                "request_id",
                None,
            ),
        )

        try:
            repository = (
                current_app.extensions.get(
                    "admin_audit_repository"
                )
            )

            if repository is None:
                repository = (
                    SQLAlchemyAdminAuditRepository()
                )

            AdminAuditService(
                repository
            ).record(event)

        except Exception as error:
            # La operación de negocio ya fue procesada por el
            # endpoint. Se informa con severidad crítica para que
            # un fallo de auditoría no pase inadvertido.
            logger.critical(
                "Admin audit write failed "
                "action=%s entity_type=%s entity_id=%s "
                "actor_id=%s request_id=%s exception_type=%s",
                description["action"],
                description["entity_type"],
                description["entity_id"],
                actor_id,
                event.request_id,
                type(error).__name__,
            )

        return response