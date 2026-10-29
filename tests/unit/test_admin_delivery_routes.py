from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app import create_app
from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)
from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)
from app.infrastructure.security.jwt_service import JWTService
from app.presentation.routes import admin_delivery_routes
from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)


class FakeAdminUserRepository:
    def get_by_id(self, user_id):
        if int(user_id) != 1:
            return None

        return SimpleNamespace(
            id=1,
            name="Administrador de prueba",
            email="admin@test.com",
            is_active=True,
            token_version=0,
        )


class FakeDeliverySettingsRepository:
    def __init__(self):
        self.settings = None

    def get_settings(self):
        return self.settings

    def save_settings(self, settings):
        settings.updated_at = datetime.now(
            timezone.utc
        )
        self.settings = settings
        return settings


def _create_test_app(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app("development")

    app.extensions["admin_user_repository"] = (
        FakeAdminUserRepository()
    )

    audit_repository = InMemoryAdminAuditRepository()

    app.extensions["admin_audit_repository"] = (
        audit_repository
    )

    settings_repository = FakeDeliverySettingsRepository()

    service = DeliveryPricingService(
        settings_repository
    )

    monkeypatch.setattr(
        admin_delivery_routes,
        "_get_service",
        lambda: service,
    )

    monkeypatch.setattr(
        JWTService,
        "decode_access_token",
        staticmethod(
            lambda token: {
                "sub": "1",
                "email": "admin@test.com",
                "token_version": 0,
            }
        ),
    )

    return (
        app,
        service,
        settings_repository,
        audit_repository,
    )


def _auth_headers():
    return {
        "Authorization": "Bearer test-token",
    }


def _valid_settings_payload():
    return {
        "origin_latitude": "6.2442000",
        "origin_longitude": "-75.5812000",
        "public_map_center_latitude": "6.2500000",
        "public_map_center_longitude": "-75.5700000",
        "base_fee": "3500.00",
        "price_per_km": "800.00",
        "distance_factor": "1.30",
        "max_distance_km": "50.00",
    }


def test_get_delivery_settings_requires_authentication(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    response = app.test_client().get(
        "/api/admin/delivery-settings"
    )

    assert response.status_code == 401


def test_put_delivery_settings_requires_authentication(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        json=_valid_settings_payload(),
    )

    assert response.status_code == 401


def test_get_delivery_settings_returns_unconfigured_defaults(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    response = app.test_client().get(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["success"] is True
    assert body["data"]["id"] == 1
    assert body["data"]["configured"] is False
    assert body["data"]["origin_latitude"] is None
    assert body["data"]["origin_longitude"] is None
    assert body["data"]["base_fee"] == "0.00"


def test_put_delivery_settings_saves_configuration(
    monkeypatch,
):
    app, _, repository, _ = _create_test_app(
        monkeypatch
    )

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
        json=_valid_settings_payload(),
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["success"] is True
    assert body["data"]["configured"] is True
    assert body["data"]["base_fee"] == "3500.00"
    assert body["data"]["price_per_km"] == "800.00"
    assert body["data"]["distance_factor"] == "1.30"
    assert body["data"]["max_distance_km"] == "50.00"

    assert repository.settings is not None
    assert repository.settings.origin_latitude == (
        Decimal("6.2442000")
    )


def test_put_delivery_settings_rejects_invalid_json(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_REQUEST"


def test_put_delivery_settings_rejects_invalid_factor(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    payload = _valid_settings_payload()
    payload["distance_factor"] = "4.00"

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
        json=payload,
    )

    assert response.status_code == 400

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "INVALID_DELIVERY_SETTINGS"
    )


def test_put_delivery_settings_rejects_public_center_equal_to_origin(
    monkeypatch,
):
    app, *_ = _create_test_app(monkeypatch)

    payload = _valid_settings_payload()
    payload["public_map_center_latitude"] = (
        payload["origin_latitude"]
    )
    payload["public_map_center_longitude"] = (
        payload["origin_longitude"]
    )

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
        json=payload,
    )

    assert response.status_code == 400

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "INVALID_DELIVERY_SETTINGS"
    )


def test_put_delivery_settings_records_audit_without_coordinates(
    monkeypatch,
):
    app, _, _, audit_repository = _create_test_app(
        monkeypatch
    )

    response = app.test_client().put(
        "/api/admin/delivery-settings",
        headers=_auth_headers(),
        json=_valid_settings_payload(),
    )

    assert response.status_code == 200
    assert len(audit_repository.events) == 1

    event = audit_repository.events[0]

    assert event.action == "delivery.settings_updated"
    assert event.entity_type == "delivery_settings"

    assert event.details == {
        "delivery_settings_updated": True,
    }

    assert "6.2442000" not in str(event.details)
    assert "-75.5812000" not in str(event.details)