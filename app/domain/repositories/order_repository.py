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


    @abstractmethod
    def get_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> OrderEntity | None:
        """Busca un pedido por la clave de una solicitud anterior."""
        raise NotImplementedError

    
    @abstractmethod
    def get_by_tracking_token(
        self,
        tracking_token: str,
    ) -> OrderEntity | None:
        """Busca un pedido por su token público de seguimiento."""
        raise NotImplementedError

    
    @abstractmethod
    def update_status(
        self,
        order_id: int,
        status: str,
        *,
        actor_id: int | None = None,
        actor_name: str | None = None,
        actor_email: str | None = None,
    ) -> OrderEntity | None:
        """Actualiza el estado y registra quién realizó el cambio."""
        raise NotImplementedError


    @abstractmethod
    def get_all_paginated(
        self,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[OrderEntity], int]:
        """
        Obtiene pedidos paginados para administración.

        Retorna:
            - lista de pedidos
            - cantidad total de pedidos que cumplen los filtros
        """
        raise NotImplementedError