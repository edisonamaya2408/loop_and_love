from abc import ABC, abstractmethod
from decimal import Decimal

from app.domain.entities.product import ProductEntity


class ProductRepository(ABC):
    """Contrato para persistencia de productos."""

    @abstractmethod
    def get_by_id(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        """Obtiene un producto por ID."""
        raise NotImplementedError

    @abstractmethod
    def get_active_by_id(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        """Obtiene un producto activo por ID."""
        raise NotImplementedError

    @abstractmethod
    def get_by_code(
        self,
        code: str,
    ) -> ProductEntity | None:
        """Obtiene un producto por código."""
        raise NotImplementedError

    @abstractmethod
    def get_active(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> list[ProductEntity]:
        """Obtiene productos activos aplicando filtros."""
        raise NotImplementedError

    @abstractmethod
    def get_active_paginated(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[ProductEntity], int]:
        """
        Obtiene productos activos paginados.

        Retorna:
            - lista de productos
            - cantidad total de productos que cumplen los filtros
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_paginated(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[ProductEntity], int]:
        """
        Obtiene productos para administración de forma paginada.

        is_active:
            - True: únicamente activos.
            - False: únicamente inactivos.
            - None: activos e inactivos.

        Retorna:
            - lista de productos
            - cantidad total que cumple los filtros
        """
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[ProductEntity]:
        """Obtiene todos los productos."""
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        product: ProductEntity,
    ) -> ProductEntity:
        """Crea un producto."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        product: ProductEntity,
    ) -> ProductEntity:
        """Actualiza un producto."""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        """
        Elimina un producto y retorna la entidad eliminada.

        Retorna None si el producto no existe.
        """
        raise NotImplementedError