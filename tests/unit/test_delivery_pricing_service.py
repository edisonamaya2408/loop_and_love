from decimal import Decimal

import pytest

from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)
from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)
from app.domain.exceptions import (
    DeliveryOutsideCoverageError,
    DeliverySettingsNotConfiguredError,
)


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


def test_delivery_quote_applies_base_fee_and_distance_rate():
    service = DeliveryPricingService(
        FakeDeliverySettingsRepository(
            configured_settings()
        )
    )

    quote = service.quote(
        "6.2542000",
        "-75.5812000",
    )

    assert quote["straight_distance_km"] > Decimal("0")
    assert quote["distance_km"] >= quote["straight_distance_km"]

    assert quote["billable_km"] >= 1

    assert quote["delivery_fee"] == (
        Decimal("3500.00")
        + Decimal("800.00") * quote["billable_km"]
    )


def test_delivery_quote_rejects_unconfigured_origin():
    service = DeliveryPricingService(
        FakeDeliverySettingsRepository()
    )

    with pytest.raises(DeliverySettingsNotConfiguredError):
        service.quote("6.2442000", "-75.5812000")


def test_delivery_quote_rejects_destination_outside_coverage():
    settings = configured_settings()
    settings.max_distance_km = Decimal("1.00")

    service = DeliveryPricingService(
        FakeDeliverySettingsRepository(settings)
    )

    with pytest.raises(DeliveryOutsideCoverageError):
        service.quote(
            "6.3000000",
            "-75.5000000",
        )


@pytest.mark.parametrize(
    ("latitude", "longitude"),
    [
        ("91", "0"),
        ("0", "181"),
        ("NaN", "0"),
        (True, "0"),
        ("6.2442", None),
    ],
)
def test_delivery_quote_rejects_invalid_coordinates(
    latitude,
    longitude,
):
    service = DeliveryPricingService(
        FakeDeliverySettingsRepository(
            configured_settings()
        )
    )

    with pytest.raises(ValueError):
        service.quote(latitude, longitude)


def test_public_map_config_does_not_expose_private_origin():
    service = DeliveryPricingService(
        FakeDeliverySettingsRepository(
            configured_settings()
        )
    )

    config = service.get_public_map_config()

    assert "origin_latitude" not in config
    assert "origin_longitude" not in config

    assert (
        config["map_center_latitude"]
        == Decimal("6.2500000")
    )


def test_save_settings_rejects_public_center_near_origin():
    repository = FakeDeliverySettingsRepository()

    service = DeliveryPricingService(repository)

    with pytest.raises(
        ValueError,
        match="al menos a 1 km",
    ):
        service.save_settings(
            {
                "origin_latitude": "6.2442000",
                "origin_longitude": "-75.5812000",
                "public_map_center_latitude": "6.2443000",
                "public_map_center_longitude": "-75.5812000",
                "base_fee": "3500.00",
                "price_per_km": "800.00",
                "distance_factor": "1.30",
                "max_distance_km": "50.00",
            }
        )