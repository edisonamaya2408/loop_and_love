import json

import pytest

from flask import (
    Flask,
    g,
    jsonify,
    request,
)
import app.presentation.middleware.admin_audit_middleware as audit_middleware

from app.presentation.middleware.admin_audit_middleware import (
    register_admin_audit,
)
from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)
from app.presentation.middleware.admin_audit_middleware import (
    _build_field_changes,
    register_admin_audit,
)


def _create_audit_test_app():
    app = Flask(__name__)

    repository = (
        InMemoryAdminAuditRepository()
    )

    app.extensions[
        "admin_audit_repository"
    ] = repository

    @app.before_request
    def set_test_actor():
        g.request_id = "audit-test-request"

        if request.path.startswith(
            "/api/admin/"
        ):
            g.authenticated_user = {
                "id": 7,
                "name": "María Gómez",
                "email": "maria@example.com",
            }

    @app.route(
        "/api/admin/<resource>",
        methods=["POST"],
    )
    def create_resource(resource):
        payload = (
            request.get_json(silent=True)
            or {}
        )

        if payload.get("force_error"):
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Error simulado.",
                    },
                }
            ), 400

        data = {
            "id": 101,
            "name": payload.get(
                "name",
                "Registro de prueba",
            ),
            "is_active": payload.get(
                "is_active",
                True,
            ),
        }

        if resource == "products":
            data["code"] = payload.get(
                "code",
                "LL-001",
            )

        if resource == "categories":
            data["slug"] = "categoria-prueba"

        if resource == "users":
            data["email"] = payload.get(
                "email",
                "nuevo@example.com",
            )

        return jsonify(
            {
                "success": True,
                "data": data,
            }
        ), 201

    @app.route(
        "/api/admin/<resource>",
        methods=["GET"],
    )
    def list_resource(resource):
        return jsonify(
            {
                "success": True,
                "data": [],
            }
        ), 200

    @app.route(
        "/api/admin/<resource>/<int:record_id>",
        methods=[
            "PUT",
            "PATCH",
            "DELETE",
        ],
    )
    def mutate_resource(
        resource,
        record_id,
    ):
        payload = (
            request.get_json(silent=True)
            or {}
        )

        data = {
            "id": record_id,
            "name": payload.get(
                "name",
                "Registro de prueba",
            ),
            "is_active": payload.get(
                "is_active",
                True,
            ),
        }

        if resource == "products":
            data["code"] = "LL-001"

        if resource == "categories":
            data["slug"] = "categoria-prueba"

        if resource == "users":
            data["email"] = payload.get(
                "email",
                "usuario@example.com",
            )

        return jsonify(
            {
                "success": True,
                "data": data,
            }
        ), 200

    @app.route(
        "/api/admin/<resource>/<int:record_id>/<suffix>",
        methods=[
            "PATCH",
            "DELETE",
        ],
    )
    def mutate_subresource(
        resource,
        record_id,
        suffix,
    ):
        payload = (
            request.get_json(silent=True)
            or {}
        )

        if (
            resource == "orders"
            and suffix == "status"
        ):
            status = payload.get(
                "status",
                "confirmed",
            )

            return jsonify(
                {
                    "success": True,
                    "data": {
                        "id": record_id,
                        "status": status,
                        "status_history": [
                            {
                                "previous_status": "pending",
                                "new_status": status,
                            }
                        ],
                    },
                }
            ), 200

        if (
            resource == "products"
            and suffix == "status"
        ):
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "id": record_id,
                        "name": "Producto de prueba",
                        "is_active": payload.get(
                            "is_active",
                            False,
                        ),
                    },
                }
            ), 200

        return jsonify(
            {
                "success": True,
                "data": {
                    "id": record_id,
                    "name": "Registro de prueba",
                },
            }
        ), 200

    @app.post("/api/orders")
    def create_public_order():
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": 501,
                },
            }
        ), 201
    
    @app.route("/api/admin/orders/<int:order_id>/tracking-token/rotate",methods=["POST"],)
    def rotate_tracking_token(order_id):
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": order_id,
                    "status": "pending",
                    "tracking_token": (
                        "secret-token-not-for-audit"
                    ),
                },
            }
        ), 200

    @app.route(
    "/api/admin/orders/<int:order_id>/status-notification/prepared",
    methods=["POST"],
    )
    def prepare_status_notification(order_id):
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": order_id,
                    "status": "preparing",
                    "whatsapp_notification_prepared": True,
                    "tracking_token": "secret-token-not-for-audit",
                },
            }
        ), 200

    register_admin_audit(
        app
    )

    return app, repository


def test_audit_records_product_creation_and_redacts_password():
    app, repository = (
        _create_audit_test_app()
    )

    response = app.test_client().post(
        "/api/admin/products",
        json={
            "name": "Amigurumi Oso",
            "code": "LL-001",
            "password": "PasswordSuperSecreto123!",
        },
    )

    assert response.status_code == 201
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.actor_id == 7
    assert event.actor_name == "María Gómez"
    assert event.actor_email == "maria@example.com"

    assert event.action == "product.created"
    assert event.entity_type == "product"
    assert event.entity_id == "101"

    assert (
        event.details["fields"]["name"]
        == "Amigurumi Oso"
    )

    assert (
        event.details["fields"]["code"]
        == "LL-001"
    )

    assert (
        event.details["fields"]["credentials_changed"]
        is True
    )

    serialized_details = json.dumps(
        event.details,
        ensure_ascii=False,
    )

    assert (
        "PasswordSuperSecreto123!"
        not in serialized_details
    )

    assert (
        "audit-test-request"
        == event.request_id
    )


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "payload",
        "expected_action",
        "expected_type",
        "expected_id",
    ),
    [
        (
            "PUT",
            "/api/admin/products/18",
            {"name": "Nuevo nombre"},
            "product.updated",
            "product",
            "18",
        ),
        (
            "PATCH",
            "/api/admin/products/18/status",
            {"is_active": False},
            "product.deactivated",
            "product",
            "18",
        ),
        (
            "DELETE",
            "/api/admin/products/18/image",
            None,
            "product.image_deleted",
            "product",
            "18",
        ),
        (
            "DELETE",
            "/api/admin/products/18",
            None,
            "product.deleted",
            "product",
            "18",
        ),
        (
            "POST",
            "/api/admin/categories",
            {"name": "Amigurumis"},
            "category.created",
            "category",
            "101",
        ),
        (
            "PUT",
            "/api/admin/categories/8",
            {"name": "Amigurumis nuevos"},
            "category.updated",
            "category",
            "8",
        ),
        (
            "DELETE",
            "/api/admin/categories/8",
            None,
            "category.deleted",
            "category",
            "8",
        ),
        (
            "POST",
            "/api/admin/users",
            {
                "name": "Carlos",
                "email": "carlos@example.com",
                "password": "Password123!",
            },
            "admin_user.created",
            "admin_user",
            "101",
        ),
        (
            "PATCH",
            "/api/admin/users/4",
            {"is_active": False},
            "admin_user.deactivated",
            "admin_user",
            "4",
        ),
        (
            "POST",
            "/api/admin/orders/18/tracking-token/rotate",
            None,
            "order.tracking_token_rotated",
            "order",
            "18",
        ),
        (
            "POST",
            "/api/admin/orders/18/status-notification/prepared",
            None,
            "order.whatsapp_notification_prepared",
            "order",
            "18",
        ),
    ],
)
def test_audit_classifies_admin_mutations(
    method,
    path,
    payload,
    expected_action,
    expected_type,
    expected_id,
):
    app, repository = (
        _create_audit_test_app()
    )

    kwargs = {}

    if payload is not None:
        kwargs["json"] = payload

    response = app.test_client().open(
        path,
        method=method,
        **kwargs,
    )

    assert 200 <= response.status_code < 300
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.action == expected_action
    assert event.entity_type == expected_type
    assert event.entity_id == expected_id
    assert event.actor_id == 7


def test_audit_records_order_status_change():
    app, repository = (
        _create_audit_test_app()
    )

    response = app.test_client().patch(
        "/api/admin/orders/15/status",
        json={
            "status": "confirmed",
        },
    )

    assert response.status_code == 200
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.action == "order.confirmed"
    assert event.entity_type == "order"
    assert event.entity_id == "15"

    assert (
        event.details["previous_status"]
        == "pending"
    )

    assert (
        event.details["new_status"]
        == "confirmed"
    )


def test_audit_does_not_record_failed_mutations():
    app, repository = (
        _create_audit_test_app()
    )

    response = app.test_client().post(
        "/api/admin/products",
        json={
            "force_error": True,
        },
    )

    assert response.status_code == 400
    assert repository.events == []


def test_audit_does_not_record_public_order_creation():
    app, repository = (
        _create_audit_test_app()
    )

    response = app.test_client().post(
        "/api/orders",
        json={
            "name": "Cliente B2B",
        },
    )

    assert response.status_code == 201
    assert repository.events == []


def test_audit_does_not_record_admin_list_queries():
    app, repository = (
        _create_audit_test_app()
    )

    response = app.test_client().get(
        "/api/admin/orders"
    )

    assert response.status_code == 200
    assert repository.events == []



def test_audit_field_changes_only_contains_modified_values():
    before = {
        "id": 10,
        "name": "Bolso beige",
        "price": "85000.00",
        "is_active": True,
    }

    after = {
        "id": 10,
        "name": "Bolso artesanal beige",
        "price": "95000.00",
        "is_active": True,
    }

    changes = _build_field_changes(
        before,
        after,
    )

    assert changes == {
        "name": {
            "before": "Bolso beige",
            "after": "Bolso artesanal beige",
        },
        "price": {
            "before": "85000.00",
            "after": "95000.00",
        },
    }


def test_audit_field_changes_handles_creation():
    after = {
        "id": 10,
        "name": "Amigurumi",
    }

    changes = _build_field_changes(
        None,
        after,
    )

    assert changes == {
        "id": {
            "before": None,
            "after": 10,
        },
        "name": {
            "before": None,
            "after": "Amigurumi",
        },
    }


def test_audit_field_changes_handles_deletion():
    before = {
        "id": 10,
        "name": "Amigurumi",
    }

    changes = _build_field_changes(
        before,
        None,
    )

    assert changes == {
        "id": {
            "before": 10,
            "after": None,
        },
        "name": {
            "before": "Amigurumi",
            "after": None,
        },
    }


def test_audit_field_changes_returns_empty_when_unchanged():
    values = {
        "id": 10,
        "name": "Amigurumi",
        "is_active": True,
    }

    assert _build_field_changes(
        values,
        values.copy(),
    ) == {}



def test_audit_marks_credential_change_without_storing_secret(
    monkeypatch,
):
    app, repository = _create_audit_test_app()

    # Activa el flujo de comparación sin depender de una
    # conexión real a la base en esta prueba unitaria.
    app.extensions["sqlalchemy"] = object()

    snapshot = {
        "name": "Carlos",
        "email": "carlos@example.com",
        "is_active": True,
    }

    monkeypatch.setattr(
        audit_middleware,
        "_snapshot_entity",
        lambda entity_type, entity_id: snapshot.copy(),
    )

    secret = "ClaveSuperSecreta-NoRegistrar"

    response = app.test_client().patch(
        "/api/admin/users/4",
        json={
            "email": "carlos@example.com",
            "password": secret,
        },
    )

    assert response.status_code == 200
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.action == "admin_user.updated"
    assert event.details["credentials_changed"] is True

    serialized_details = json.dumps(
        event.details,
        ensure_ascii=False,
    )

    assert secret not in serialized_details
    assert "password_hash" not in serialized_details


def test_audit_tracking_token_rotation_never_stores_token():
    app, repository = _create_audit_test_app()

    # Simular la presencia de SQLAlchemy para verificar
    # el flujo de auditoría utilizado en producción.
    # La rotación no debe activar la comparación genérica.
    app.extensions["sqlalchemy"] = object()

    response = app.test_client().post(
        "/api/admin/orders/15/tracking-token/rotate"
    )

    assert response.status_code == 200
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.action == "order.tracking_token_rotated"

    serialized_details = json.dumps(
        event.details,
        ensure_ascii=False,
    )

    assert "secret-token-not-for-audit" not in serialized_details
    assert event.details["tracking_token_rotated"] is True


def test_audit_records_notification_prepared_without_sensitive_data():
    app, repository = _create_audit_test_app()

    app.extensions["sqlalchemy"] = object()

    response = app.test_client().post(
        "/api/admin/orders/18/status-notification/prepared"
    )

    assert response.status_code == 200
    assert len(repository.events) == 1

    event = repository.events[0]

    assert event.action == (
        "order.whatsapp_notification_prepared"
    )

    assert event.entity_type == "order"
    assert event.entity_id == "18"

    assert event.details == {
        "whatsapp_notification_prepared": True,
        "status": "preparing",
    }

    serialized_details = json.dumps(
        event.details,
        ensure_ascii=False,
    )

    assert "secret-token-not-for-audit" not in serialized_details
    assert "tracking_token" not in serialized_details