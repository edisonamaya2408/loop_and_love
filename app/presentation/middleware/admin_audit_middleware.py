import logging

from urllib.parse import urlsplit, urlunsplit

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



_AUDIT_SNAPSHOT_FIELDS = {
    "product": (
        "id",
        "code",
        "name",
        "description",
        "price",
        "category_id",
        "image_url",
        "is_active",
    ),
    "category": (
        "id",
        "name",
        "slug",
        "is_active",
    ),
    "admin_user": (
        "id",
        "name",
        "email",
        "is_active",
    ),
    "order": (
        "id",
        "status",
    ),
}

_AUDIT_RESOURCE_TYPES = {
    "products": "product",
    "categories": "category",
    "users": "admin_user",
    "orders": "order",
}


def _audit_scalar(value):
    """Convierte valores de modelos en valores seguros para JSON."""

    from datetime import date, datetime
    from decimal import Decimal

    if value is None or type(value) in (bool, int, float):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, str):
        return value[:600]

    return str(value)[:600]


def _audit_snapshot_value(field: str, value):
    """Normaliza los valores del snapshot para su auditoría."""

    if field == "image_url" and isinstance(value, str):
        try:
            parsed = urlsplit(value)

            value = urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    "",
                    "",
                )
            )

        except ValueError:
            # Nunca guardamos una URL potencialmente malformada.
            return "Imagen configurada"

    return _audit_scalar(value)


def _snapshot_entity(entity_type: str, entity_id):
    """
    Obtiene una copia independiente de los campos auditables.

    Si la entidad no existe, SQLAlchemy no está disponible
    o falla la lectura, devuelve None y deja evidencia en logs.
    """

    if entity_type not in _AUDIT_SNAPSHOT_FIELDS:
        return None

    if entity_id is None:
        return None

    try:
        numeric_id = int(entity_id)
    except (TypeError, ValueError):
        return None

    if numeric_id <= 0:
        return None

    if "sqlalchemy" not in current_app.extensions:
        return None

    try:
        from app.extensions import db
        from app.infrastructure.database.models.admin_user_model import (
            AdminUser,
        )
        from app.infrastructure.database.models.category_model import (
            Category,
        )
        from app.infrastructure.database.models.order_model import (
            Order,
        )
        from app.infrastructure.database.models.product_model import (
            Product,
        )

        models = {
            "product": Product,
            "category": Category,
            "admin_user": AdminUser,
            "order": Order,
        }

        entity = db.session.get(
            models[entity_type],
            numeric_id,
            populate_existing=True,
        )

        if entity is None:
            return None

        return {
            field: _audit_snapshot_value(
                field,
                getattr(entity, field),
            )
            for field in _AUDIT_SNAPSHOT_FIELDS[entity_type]
        }

    except Exception as error:
        logger.error(
            "Admin audit snapshot read failed "
            "entity_type=%s entity_id=%s exception_type=%s",
            entity_type,
            numeric_id,
            type(error).__name__,
        )
        return None


def _build_field_changes(
    before: dict | None,
    after: dict | None,
) -> dict:
    """Construye diferencias reales sin incluir campos idénticos."""

    if before is None and after is None:
        return {}

    fields = set(before or {}) | set(after or {})
    changes = {}

    for field in sorted(fields):
        previous_value = (
            before.get(field)
            if before is not None
            else None
        )

        new_value = (
            after.get(field)
            if after is not None
            else None
        )

        if previous_value != new_value:
            changes[field] = {
                "before": previous_value,
                "after": new_value,
            }

    return changes



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

        elif (
            request.method == "POST"
            and len(tail) == 3
            and tail[1:] == [
                "tracking-token",
                "rotate",
            ]
        ):
            action = "order.tracking_token_rotated"

        elif (
            request.method == "POST"
            and len(tail) == 3
            and tail[1:] == [
                "status-notification",
                "prepared",
            ]
        ):
            action = "order.whatsapp_notification_prepared"

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

        if action == "order.tracking_token_rotated":
            details = {
                "tracking_token_rotated": True,
            }

        else:
            details = {
                "previous_status": last_history.get(
                    "previous_status"
                ),
                "new_status": status,
            }

    elif action == "order.whatsapp_notification_prepared":
        details = {
            "whatsapp_notification_prepared": True,
            "status": status,
        }

    else:
        details = {}

    # Registrar la existencia de cambios sensibles sin almacenar
    # contraseñas, hashes ni valores de credenciales.
    if fields.get("credentials_changed") is True:
        details["credentials_changed"] = True

    if fields.get("file_attached") is True:
        details["file_attached"] = True

    snapshot_enabled = getattr(
        g,
        "admin_audit_snapshot_enabled",
        False,
    )

    if action in {
        "order.tracking_token_rotated",
        "order.whatsapp_notification_prepared",
    }:
        if action == "order.tracking_token_rotated":
            details = {
                "tracking_token_rotated": True,
            }
        else:
            details = {
                "whatsapp_notification_prepared": True,
                "status": status,
            }

    elif snapshot_enabled:
        before = getattr(
            g,
            "admin_audit_before",
            None,
        )

        after = None
        comparison_valid = False

        if action.endswith(".created"):
            after = _snapshot_entity(
                entity_type,
                entity_id,
            )
            comparison_valid = after is not None

        elif action.endswith(".deleted"):
            comparison_valid = before is not None
            after = None

        elif action == "product.image_deleted":
            after = _snapshot_entity(
                entity_type,
                entity_id,
            )
            comparison_valid = (
                before is not None
                and after is not None
            )

        elif before is not None:
            after = _snapshot_entity(
                entity_type,
                entity_id,
            )
            comparison_valid = after is not None

        if comparison_valid:
            details["changes"] = _build_field_changes(
                before,
                after,
            )
            details["comparison_available"] = True

        else:
            # No presentamos datos de la petición como si fueran
            # una comparación real de valores persistidos.
            details["comparison_available"] = False

    else:
        # Compatibilidad con las pruebas unitarias que usan
        # una aplicación Flask sin SQLAlchemy inicializado.
        if entity_type != "order" and fields:
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

    
    @app.before_request
    def capture_admin_audit_before():
        """Captura el estado persistido antes de una mutación."""

        g.admin_audit_snapshot_enabled = (
            "sqlalchemy" in current_app.extensions
        )
        g.admin_audit_before = None

        if not g.admin_audit_snapshot_enabled:
            return None

        if request.method not in {
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
            len(parts) < 4
            or parts[:2] != ["api", "admin"]
            or not parts[3].isdigit()
        ):
            return None

        entity_type = _AUDIT_RESOURCE_TYPES.get(
            parts[2]
        )

        if entity_type is None:
            return None

        try:
            g.admin_audit_before = _snapshot_entity(
                entity_type,
                parts[3],
            )
        except Exception as error:
            # No interrumpimos la operación de negocio.
            # La falta de captura debe quedar visible en los logs.
            logger.error(
                "Admin audit before-snapshot failed "
                "entity_type=%s entity_id=%s exception_type=%s",
                entity_type,
                parts[3],
                type(error).__name__,
            )

        return None


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