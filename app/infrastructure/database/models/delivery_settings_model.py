from datetime import datetime, timezone

from sqlalchemy import CheckConstraint
from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class DeliverySettings(db.Model):
    """Configuración única para la tarifa de domicilio."""

    __tablename__ = "delivery_settings"

    __table_args__ = (
        CheckConstraint(
            "id = 1",
            name="ck_delivery_settings_singleton_id",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    origin_latitude = db.Column(
        db.Numeric(10, 7),
        nullable=True,
    )

    origin_longitude = db.Column(
        db.Numeric(10, 7),
        nullable=True,
    )

    public_map_center_latitude = db.Column(
        db.Numeric(10, 7),
        nullable=True,
    )

    public_map_center_longitude = db.Column(
        db.Numeric(10, 7),
        nullable=True,
    )

    base_fee = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    price_per_km = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0,
    )

    distance_factor = db.Column(
        db.Numeric(5, 2),
        nullable=False,
        default=1.30,
    )

    max_distance_km = db.Column(
        db.Numeric(8, 2),
        nullable=False,
        default=50,
    )

    updated_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )