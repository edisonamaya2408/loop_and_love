from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class PaginationMetadata:
    """Metadatos de paginación."""

    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        if self.total == 0:
            return 0

        return (
            self.total + self.per_page - 1
        ) // self.per_page

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """Resultado paginado de una consulta."""

    items: list[T]
    pagination: PaginationMetadata