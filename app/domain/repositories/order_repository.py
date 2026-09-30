from abc import ABC, abstractmethod

from app.domain.entities.order import OrderEntity


class OrderRepository(ABC):
    """Contrato para persistencia de pedidos."""

    @abstractmethod
    def create(
        self,
        order: OrderEntity,
    ) -> OrderEntity:
        """Crea un pedido y sus líneas de forma atómica."""
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        order_id: int,
    ) -> OrderEntity | None:
        """Obtiene un pedido por ID."""
        raise NotImplementedError