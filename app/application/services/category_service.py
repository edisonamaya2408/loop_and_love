from app.domain.entities.category import CategoryEntity
from app.domain.repositories.category_repository import (
    CategoryRepository,
)
from app.domain.normalization import (
    normalize_category_display_name,
)


class CategoryService:
    """Casos de uso relacionados con categorías."""

    def __init__(
        self,
        repository: CategoryRepository,
    ):
        self.repository = repository

    def get_category(
        self,
        category_id: int,
    ) -> CategoryEntity | None:
        """Obtiene una categoría por ID."""

        self._validate_id(category_id)

        return self.repository.get_by_id(
            category_id
        )

    def list_active_categories(
        self,
    ) -> list[CategoryEntity]:
        """Obtiene únicamente las categorías activas."""

        return self.repository.get_active()

    def list_all_categories(
        self,
    ) -> list[CategoryEntity]:
        """Obtiene todas las categorías."""

        return self.repository.get_all()

    def create_category(
        self,
        name: str,
        is_active: bool = True,
    ) -> CategoryEntity:
        """
        Crea una categoría.

        El slug se genera automáticamente a partir del nombre.
        """

        clean_name = self._validate_name(name)

        if not isinstance(is_active, bool):
            raise ValueError(
                "El campo is_active debe ser booleano."
            )

        existing_category = (
            self.repository.get_by_name(
                clean_name
            )
        )

        if existing_category is not None:
            raise ValueError(
                "Ya existe una categoría con ese nombre."
            )

        slug = self._generate_unique_slug(
            clean_name
        )

        category = CategoryEntity(
            id=None,
            name=clean_name,
            slug=slug,
            is_active=is_active,
        )

        return self.repository.create(
            category
        )

    def update_category(
        self,
        category_id: int,
        name: str,
        is_active: bool,
    ) -> CategoryEntity:
        """Actualiza una categoría existente."""

        self._validate_id(category_id)

        clean_name = self._validate_name(name)

        if not isinstance(is_active, bool):
            raise ValueError(
                "El campo is_active debe ser booleano."
            )

        category = self.repository.get_by_id(
            category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        category_with_same_name = (
            self.repository.get_by_name(
                clean_name
            )
        )

        if (
            category_with_same_name is not None
            and category_with_same_name.id != category_id
        ):
            raise ValueError(
                "Ya existe una categoría con ese nombre."
            )

        category.name = clean_name

        category.slug = self._generate_unique_slug(
            clean_name,
            current_category_id=category_id,
        )

        category.is_active = is_active

        return self.repository.update(
            category
        )

    def delete_category(
        self,
        category_id: int,
    ) -> CategoryEntity:
        """
        Elimina físicamente una categoría únicamente si
        no tiene productos asociados.

        Las categorías utilizadas por productos no pueden
        eliminarse para preservar la integridad del catálogo.
        En ese caso deben desactivarse mediante update_category().
        """

        self._validate_id(category_id)

        category = self.repository.get_by_id(
            category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        if self.repository.has_products(
            category_id
        ):
            raise ValueError(
                "No se puede eliminar la categoría porque "
                "tiene productos asociados. "
                "Desactívela en lugar de eliminarla."
            )

        deleted_category = (
            self.repository.delete(
                category_id
            )
        )

        if deleted_category is None:
            raise LookupError(
                "La categoría no existe."
            )

        return deleted_category

    def _generate_unique_slug(
        self,
        name: str,
        current_category_id: int | None = None,
    ) -> str:
        """
        Genera un slug único a partir del nombre.

        Ejemplo:

            Amigurumis      → amigurumis
            Amigurumis 2    → amigurumis-2
        """

        base_slug = self._slugify(name)

        if not base_slug:
            raise ValueError(
                "No fue posible generar un slug válido "
                "para la categoría."
            )

        slug = base_slug
        suffix = 2

        while True:
            existing_category = (
                self.repository.get_by_slug(
                    slug
                )
            )

            if existing_category is None:
                return slug

            if (
                current_category_id is not None
                and existing_category.id == current_category_id
            ):
                return slug

            slug = f"{base_slug}-{suffix}"
            suffix += 1

    @staticmethod
    def _slugify(
        value: str,
    ) -> str:
        """
        Convierte un nombre en un slug básico.

        Elimina acentos y deja únicamente caracteres
        alfanuméricos separados por guiones.
        """

        import re
        import unicodedata

        normalized = unicodedata.normalize(
            "NFKD",
            value,
        )

        ascii_value = normalized.encode(
            "ascii",
            "ignore",
        ).decode(
            "ascii"
        )

        slug = re.sub(
            r"[^a-zA-Z0-9]+",
            "-",
            ascii_value,
        )

        return slug.strip(
            "-"
        ).lower()

    @staticmethod
    def _validate_name(
        name: str,
    ) -> str:
        """Valida y normaliza el nombre de una categoría."""

        if not isinstance(name, str):
            raise ValueError(
                "El nombre de la categoría es obligatorio."
            )

        name = normalize_category_display_name(
            name
        )

        if not name:
            raise ValueError(
                "El nombre de la categoría es obligatorio."
            )

        if len(name) > 100:
            raise ValueError(
                "El nombre de la categoría no puede superar "
                "los 100 caracteres."
            )

        return name

    @staticmethod
    def _validate_id(
        category_id: int,
    ) -> None:
        """Valida el ID de una categoría."""

        if isinstance(
            category_id,
            bool,
        ):
            raise ValueError(
                "El ID de la categoría debe ser un número entero."
            )

        if not isinstance(
            category_id,
            int,
        ):
            raise ValueError(
                "El ID de la categoría debe ser un número entero."
            )

        if category_id <= 0:
            raise ValueError(
                "El ID de la categoría debe ser mayor que cero."
            )