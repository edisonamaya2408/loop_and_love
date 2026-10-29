import math

from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_HALF_UP,
)

from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)
from app.domain.exceptions import (
    DeliverySettingsNotConfiguredError,
    DeliveryOutsideCoverageError,
)


DISTANCE_QUANTUM = Decimal("0.01")
COORDINATE_QUANTUM = Decimal("0.0000001")
MONEY_QUANTUM = Decimal("0.01")


class DeliveryPricingService:
    """Valida tarifas y calcula cotizaciones de domicilio."""

    EARTH_RADIUS_KM = 6371.0088

    def __init__(self, repository):
        self.repository = repository

    def get_admin_settings(self):
        settings = self.repository.get_settings()

        return settings or DeliverySettingsEntity()

    @staticmethod
    def is_configured(settings):
        return all(
            value is not None
            for value in (
                settings.origin_latitude,
                settings.origin_longitude,
                settings.public_map_center_latitude,
                settings.public_map_center_longitude,
            )
        )

    @staticmethod
    def _decimal(value, field_name):
        if isinstance(value, bool) or value is None:
            raise ValueError(
                f"El campo {field_name} no es válido."
            )

        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as error:
            raise ValueError(
                f"El campo {field_name} debe ser numérico."
            ) from error

        if not number.is_finite():
            raise ValueError(
                f"El campo {field_name} no es finito."
            )

        return number

    @classmethod
    def _coordinate(
        cls,
        value,
        field_name,
        minimum,
        maximum,
    ):
        number = cls._decimal(value, field_name)

        if number < minimum or number > maximum:
            raise ValueError(
                f"El campo {field_name} está fuera de rango."
            )

        return number.quantize(COORDINATE_QUANTUM)

    @classmethod
    def normalize_coordinates(
        cls,
        latitude,
        longitude,
    ):
        return (
            cls._coordinate(
                latitude,
                "latitud",
                Decimal("-90"),
                Decimal("90"),
            ),
            cls._coordinate(
                longitude,
                "longitud",
                Decimal("-180"),
                Decimal("180"),
            ),
        )

    MIN_PUBLIC_CENTER_SEPARATION_KM = 1.0

    @classmethod
    def _straight_line_distance_km(
        cls,
        latitude_a,
        longitude_a,
        latitude_b,
        longitude_b,
    ):
        latitude_a_rad = math.radians(float(latitude_a))
        longitude_a_rad = math.radians(float(longitude_a))
        latitude_b_rad = math.radians(float(latitude_b))
        longitude_b_rad = math.radians(float(longitude_b))

        latitude_delta = (
            latitude_b_rad - latitude_a_rad
        )

        longitude_delta = (
            longitude_b_rad - longitude_a_rad
        )

        haversine = (
            math.sin(latitude_delta / 2) ** 2
            + math.cos(latitude_a_rad)
            * math.cos(latitude_b_rad)
            * math.sin(longitude_delta / 2) ** 2
        )

        haversine = min(
            1.0,
            max(0.0, haversine),
        )

        return (
            2
            * cls.EARTH_RADIUS_KM
            * math.asin(math.sqrt(haversine))
        )

    @classmethod
    def _money(cls, value, field_name):
        number = cls._decimal(value, field_name)

        if number < 0 or number > Decimal("100000000"):
            raise ValueError(
                f"El campo {field_name} está fuera de rango."
            )

        return number.quantize(MONEY_QUANTUM)

    def save_settings(self, data):
        if not isinstance(data, dict):
            raise ValueError(
                "La configuración debe ser un objeto JSON."
            )

        allowed_fields = {
            "origin_latitude",
            "origin_longitude",
            "public_map_center_latitude",
            "public_map_center_longitude",
            "base_fee",
            "price_per_km",
            "distance_factor",
            "max_distance_km",
        }

        unexpected_fields = set(data) - allowed_fields

        if unexpected_fields:
            raise ValueError(
                "La configuración contiene campos no permitidos."
            )

        origin_latitude, origin_longitude = (
            self.normalize_coordinates(
                data.get("origin_latitude"),
                data.get("origin_longitude"),
            )
        )

        public_latitude, public_longitude = (
            self.normalize_coordinates(
                data.get("public_map_center_latitude"),
                data.get("public_map_center_longitude"),
            )
        )

        center_separation_km = (
            self._straight_line_distance_km(
                origin_latitude,
                origin_longitude,
                public_latitude,
                public_longitude,
            )
        )

        if (
            center_separation_km
            < self.MIN_PUBLIC_CENTER_SEPARATION_KM
        ):
            raise ValueError(
                "El centro público del mapa debe estar al "
                "menos a 1 km de la ubicación privada de origen."
            )

        base_fee = self._money(
            data.get("base_fee"),
            "domicilio base",
        )

        price_per_km = self._money(
            data.get("price_per_km"),
            "valor por kilómetro",
        )

        distance_factor = self._decimal(
            data.get("distance_factor"),
            "factor de recorrido",
        )

        max_distance_km = self._decimal(
            data.get("max_distance_km"),
            "distancia máxima",
        )

        if not Decimal("1") <= distance_factor <= Decimal("3"):
            raise ValueError(
                "El factor de recorrido debe estar entre 1 y 3."
            )

        if not Decimal("1") <= max_distance_km <= Decimal("300"):
            raise ValueError(
                "La distancia máxima debe estar entre 1 y 300 km."
            )

        settings = DeliverySettingsEntity(
            id=1,
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            public_map_center_latitude=public_latitude,
            public_map_center_longitude=public_longitude,
            base_fee=base_fee,
            price_per_km=price_per_km,
            distance_factor=distance_factor.quantize(
                Decimal("0.01")
            ),
            max_distance_km=max_distance_km.quantize(
                Decimal("0.01")
            ),
        )

        return self.repository.save_settings(settings)

    def get_public_map_config(self):
        settings = self.get_admin_settings()

        if not self.is_configured(settings):
            raise DeliverySettingsNotConfiguredError()

        # No devolver las coordenadas exactas de origen.
        return {
            "map_center_latitude": (
                settings.public_map_center_latitude
            ),
            "map_center_longitude": (
                settings.public_map_center_longitude
            ),
            "max_distance_km": settings.max_distance_km,
        }

    def quote(self, latitude, longitude):
        settings = self.get_admin_settings()

        if not self.is_configured(settings):
            raise DeliverySettingsNotConfiguredError()

        destination_latitude, destination_longitude = (
            self.normalize_coordinates(
                latitude,
                longitude,
            )
        )

        origin_latitude = float(settings.origin_latitude)
        origin_longitude = float(settings.origin_longitude)

        destination_latitude_float = float(destination_latitude)
        destination_longitude_float = float(destination_longitude)

        latitude_delta = math.radians(
            destination_latitude_float - origin_latitude
        )

        longitude_delta = math.radians(
            destination_longitude_float - origin_longitude
        )

        origin_latitude_rad = math.radians(origin_latitude)
        destination_latitude_rad = math.radians(
            destination_latitude_float
        )

        haversine = (
            math.sin(latitude_delta / 2) ** 2
            + math.cos(origin_latitude_rad)
            * math.cos(destination_latitude_rad)
            * math.sin(longitude_delta / 2) ** 2
        )

        haversine = min(
            1.0,
            max(0.0, haversine),
        )

        straight_distance = (
            2
            * self.EARTH_RADIUS_KM
            * math.asin(math.sqrt(haversine))
        )

        straight_distance_km = Decimal(
            str(straight_distance)
        ).quantize(
            DISTANCE_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

        estimated_distance_km = (
            straight_distance_km
            * settings.distance_factor
        ).quantize(
            DISTANCE_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

        if estimated_distance_km > settings.max_distance_km:
            raise DeliveryOutsideCoverageError()

        billable_km = math.ceil(
            estimated_distance_km
        )

        delivery_fee = (
            settings.base_fee
            + settings.price_per_km * billable_km
        ).quantize(
            MONEY_QUANTUM,
            rounding=ROUND_HALF_UP,
        )

        return {
            "latitude": destination_latitude,
            "longitude": destination_longitude,
            "straight_distance_km": straight_distance_km,
            "distance_km": estimated_distance_km,
            "billable_km": billable_km,
            "delivery_fee": delivery_fee,
            "base_fee": settings.base_fee,
            "price_per_km": settings.price_per_km,
            "distance_factor": settings.distance_factor,
        }