from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)
from app.domain.repositories.delivery_settings_repository import (
    DeliverySettingsRepository,
)
from app.extensions import db
from app.infrastructure.database.models.delivery_settings_model import (
    DeliverySettings,
)


class SQLAlchemyDeliverySettingsRepository(
    DeliverySettingsRepository
):
    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(model):
        return DeliverySettingsEntity(
            id=model.id,
            origin_latitude=(
                Decimal(str(model.origin_latitude))
                if model.origin_latitude is not None
                else None
            ),
            origin_longitude=(
                Decimal(str(model.origin_longitude))
                if model.origin_longitude is not None
                else None
            ),
            public_map_center_latitude=(
                Decimal(str(model.public_map_center_latitude))
                if model.public_map_center_latitude is not None
                else None
            ),
            public_map_center_longitude=(
                Decimal(str(model.public_map_center_longitude))
                if model.public_map_center_longitude is not None
                else None
            ),
            base_fee=Decimal(str(model.base_fee)),
            price_per_km=Decimal(str(model.price_per_km)),
            distance_factor=Decimal(str(model.distance_factor)),
            max_distance_km=Decimal(str(model.max_distance_km)),
            updated_at=model.updated_at,
        )

    def get_settings(self):
        model = self.session.get(
            DeliverySettings,
            1,
        )

        if model is None:
            return None

        return self._to_entity(model)

    def save_settings(self, settings):
        model = self.session.get(
            DeliverySettings,
            1,
        )

        if model is None:
            model = DeliverySettings(id=1)

        model.origin_latitude = settings.origin_latitude
        model.origin_longitude = settings.origin_longitude

        model.public_map_center_latitude = (
            settings.public_map_center_latitude
        )
        model.public_map_center_longitude = (
            settings.public_map_center_longitude
        )

        model.base_fee = settings.base_fee
        model.price_per_km = settings.price_per_km
        model.distance_factor = settings.distance_factor
        model.max_distance_km = settings.max_distance_km
        model.updated_at = datetime.now(timezone.utc)

        self.session.add(model)

        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return self._to_entity(model)