from decimal import Decimal

from app import create_app
from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)
from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)
from app.presentation.routes import delivery_routes


class FakeDeliverySettingsRepository:
    def __init__(self, settings=None):
        self.settings = settings

    def get_settings(self):
        return self.settings

    def save_settings(self, settings):
        self.settings = settings
        return settings


def configured_settings():
    return DeliverySettingsEntity(
        id=1,
        origin_latitude=Decimal("6.2442000"),
        origin_longitude=Decimal("-75.5812000"),
        public_map_center_latitude=Decimal("6.2500000"),
        public_map_center_longitude=Decimal("-75.5700000"),
        base_fee=Decimal("3500.00"),
        price_per_km=Decimal("800.00"),
        distance_factor=Decimal("1.30"),
        max_distance_km=Decimal("50.00"),
    )


def _create_test_app(monkeypatch, settings=None):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app("development")

    repository = FakeDeliverySettingsRepository(
        settings=settings
    )

    service = DeliveryPricingService(repository)

    monkeypatch.setattr(
        delivery_routes,
        "_get_service",
        lambda: service,
    )

    return app


def test_public_delivery_config_does_not_expose_origin(
    monkeypatch,
):
    app = _create_test_app(
        monkeypatch,
        settings=configured_settings(),
    )

    response = app.test_client().get(
        "/api/delivery/config"
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["success"] is True

    assert set(body["data"]) == {
        "map_center_latitude",
        "map_center_longitude",
        "max_distance_km",
    }

    assert "origin_latitude" not in body["data"]
    assert "origin_longitude" not in body["data"]


def test_public_delivery_quote_returns_fee_only(
    monkeypatch,
):
    app = _create_test_app(
        monkeypatch,
        settings=configured_settings(),
    )

    response = app.test_client().post(
        "/api/delivery/quote",
        json={
            "latitude": 6.2542000,
            "longitude": -75.5812000,
        },
    )

    assert response.status_code == 200

    body = response.get_json()

    assert body["success"] is True

    assert set(body["data"]) == {
        "delivery_fee",
        "currency",
    }

    assert body["data"]["currency"] == "COP"


def test_public_delivery_quote_rejects_invalid_coordinates(
    monkeypatch,
):
    app = _create_test_app(
        monkeypatch,
        settings=configured_settings(),
    )

    response = app.test_client().post(
        "/api/delivery/quote",
        json={
            "latitude": 91,
            "longitude": -75.5,
        },
    )

    assert response.status_code == 400

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "INVALID_DELIVERY_LOCATION"
    )


def test_public_delivery_quote_rejects_outside_coverage(
    monkeypatch,
):
    settings = configured_settings()
    settings.max_distance_km = Decimal("1.00")

    app = _create_test_app(
        monkeypatch,
        settings=settings,
    )

    response = app.test_client().post(
        "/api/delivery/quote",
        json={
            "latitude": 6.3000000,
            "longitude": -75.5000000,
        },
    )

    assert response.status_code == 422

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "DELIVERY_OUT_OF_COVERAGE"
    )


def test_public_delivery_config_returns_unavailable_when_unconfigured(
    monkeypatch,
):
    app = _create_test_app(monkeypatch)

    response = app.test_client().get(
        "/api/delivery/config"
    )

    assert response.status_code == 503

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "DELIVERY_NOT_CONFIGURED"
    )