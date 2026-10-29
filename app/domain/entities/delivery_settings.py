from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class DeliverySettingsEntity:
    id: int = 1

    origin_latitude: Decimal | None = None
    origin_longitude: Decimal | None = None

    public_map_center_latitude: Decimal | None = None
    public_map_center_longitude: Decimal | None = None

    base_fee: Decimal = Decimal("0.00")
    price_per_km: Decimal = Decimal("0.00")
    distance_factor: Decimal = Decimal("1.30")
    max_distance_km: Decimal = Decimal("50.00")

    updated_at: datetime | None = None