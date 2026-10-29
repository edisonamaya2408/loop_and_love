from abc import ABC, abstractmethod

from app.domain.entities.delivery_settings import (
    DeliverySettingsEntity,
)


class DeliverySettingsRepository(ABC):

    @abstractmethod
    def get_settings(self) -> DeliverySettingsEntity | None:
        raise NotImplementedError

    @abstractmethod
    def save_settings(
        self,
        settings: DeliverySettingsEntity,
    ) -> DeliverySettingsEntity:
        raise NotImplementedError