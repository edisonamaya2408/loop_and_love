from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app import create_app
from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)
from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)


class FakeAdminUserRepository:
    def __init__(self):
        self.user = SimpleNamespace(
            id=1,
            name="María Gómez",
            email="maria@example.com",
            is_active=True,
            token_version=0,
        )

    def get_by_id(self, user_id):
        return self.user if user_id == self.user.id else None


def _event(
    *,
    event_id,
    actor_name="María Gómez",
    actor_email="maria@example.com",
    action="product.created",
    entity_type="product",
    entity_id="10",
    created_at=None,
):
    return AdminAuditEventEntity(
        id=event_id,
        actor_id=1,
        actor_name=actor_name,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details={"result": {"name": "Producto de prueba"}},
        ip_address="127.0.0.1",
        request_id=f"request-{event_id}",
        created_at=(
            created_at
            or datetime(
                2026, 10, 9, 15, 0,
                tzinfo=timezone.utc,
            )
        ),
    )


def _create_test_app(monkeypatch, events=None):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app("development")

    audit_repository = InMemoryAdminAuditRepository()
    audit_repository.events = list(events or [])

    app.extensions["admin_audit_repository"] = audit_repository
    app.extensions["admin_user_repository"] = FakeAdminUserRepository()

    monkeypatch.setattr(
        JWTService,
        "decode_access_token",
        lambda token: {
            "sub": "1",
            "email": "maria@example.com",
            "token_version": 0,
        },
    )

    return app, audit_repository


def _headers():
    return {
        "Authorization": "Bearer test-token",
    }


def test_admin_audit_route_requires_authentication(monkeypatch):
    app, _ = _create_test_app(monkeypatch)

    response = app.test_client().get(
        "/api/admin/audit-logs"
    )

    assert response.status_code == 401


def test_list_admin_audit_logs_returns_paginated_events(monkeypatch):
    events = [
        _event(event_id=1),
        _event(
            event_id=2,
            action="order.confirmed",
            entity_type="order",
            entity_id="25",
            created_at=datetime(
                2026, 10, 9, 16, 0,
                tzinfo=timezone.utc,
            ),
        ),
    ]

    app, _ = _create_test_app(monkeypatch, events)

    response = app.test_client().get(
        "/api/admin/audit-logs?page=1&per_page=1",
        headers=_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["id"] == 2

    assert payload["pagination"] == {
        "page": 1,
        "per_page": 1,
        "total": 2,
        "pages": 2,
        "has_next": True,
        "has_previous": False,
    }


def test_list_admin_audit_logs_filters_actor_action_entity_and_id(monkeypatch):
    events = [
        _event(event_id=1),
        _event(
            event_id=2,
            actor_name="Carlos Pérez",
            actor_email="carlos@example.com",
            action="order.confirmed",
            entity_type="order",
            entity_id="25",
        ),
    ]

    app, _ = _create_test_app(monkeypatch, events)

    response = app.test_client().get(
        (
            "/api/admin/audit-logs?"
            "actor=Carlos&action=order.confirmed&"
            "entity_type=order&entity_id=25"
        ),
        headers=_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["pagination"]["total"] == 1
    assert payload["data"][0]["actor_name"] == "Carlos Pérez"
    assert payload["data"][0]["action"] == "order.confirmed"
    assert payload["data"][0]["entity_id"] == "25"


@pytest.mark.parametrize(
    "query_string",
    [
        "?date_from=no-es-fecha",
        "?date_from=2026-10-10&date_to=2026-10-09",
        "?action=unknown.action",
        "?entity_type=unknown",
        "?page=0",
        "?per_page=500",
    ],
)
def test_list_admin_audit_logs_rejects_invalid_filters(
    monkeypatch,
    query_string,
):
    app, _ = _create_test_app(monkeypatch)

    response = app.test_client().get(
        f"/api/admin/audit-logs{query_string}",
        headers=_headers(),
    )

    assert response.status_code == 400
    assert (
        response.get_json()["error"]["code"]
        == "INVALID_AUDIT_FILTERS"
    )