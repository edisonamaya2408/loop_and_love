from abc import ABC, abstractmethod

from app.domain.entities.category import CategoryEntity


class CategoryRepository(ABC):
    """Contrato para persistencia de categorías."""

    @abstractmethod
    def get_by_id(
        self,
        category_id: int,
    ) -> CategoryEntity | None:
        """Obtiene una categoría por ID."""
        raise NotImplementedError

    @abstractmethod
    def get_by_ids(
        self,
        category_ids: list[int] | set[int],
    ) -> dict[int, CategoryEntity]:
        """
        Obtiene múltiples categorías en una sola operación.

        La clave del diccionario es el ID de la categoría.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_name(
        self,
        name: str,
    ) -> CategoryEntity | None:
        """Obtiene una categoría por nombre."""
        raise NotImplementedError

    @abstractmethod
    def get_by_slug(
        self,
        slug: str,
    ) -> CategoryEntity | None:
        """Obtiene una categoría por slug."""
        raise NotImplementedError

    @abstractmethod
    def get_active(self) -> list[CategoryEntity]:
        """Obtiene únicamente las categorías activas."""
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[CategoryEntity]:
        """Obtiene todas las categorías."""
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        category: CategoryEntity,
    ) -> CategoryEntity:
        """Crea una categoría."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        category: CategoryEntity,
    ) -> CategoryEntity | None:
        """Actualiza una categoría."""
        raise NotImplementedError

    @abstractmethod
    def has_products(
        self,
        category_id: int,
    ) -> bool:
        """
        Indica si existen productos asociados
        a la categoría.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        category_id: int,
    ) -> CategoryEntity | None:
        """
        Elimina una categoría.

        Retorna None si no existe.
        """
        raise NotImplementedError