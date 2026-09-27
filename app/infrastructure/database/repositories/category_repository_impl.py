from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.category import CategoryEntity
from app.domain.exceptions import (
    DuplicateCategoryNameError,
    DuplicateCategorySlugError,
)
from app.domain.repositories.category_repository import (
    CategoryRepository,
)
from app.extensions import db
from app.infrastructure.database.integrity import (
    is_category_name_integrity_error,
    is_category_slug_integrity_error,
)
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product
from app.domain.normalization import (
    normalize_category_name,
)


class SQLAlchemyCategoryRepository(CategoryRepository):
    """Implementación del repositorio de categorías usando SQLAlchemy."""

    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(
        model: Category,
    ) -> CategoryEntity:
        return CategoryEntity(
            id=model.id,
            name=model.name,
            slug=model.slug,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(
        self,
        category_id: int,
    ) -> CategoryEntity | None:
        model = self.session.get(
            Category,
            category_id,
        )

        if model is None:
            return None

        return self._to_entity(model)

    def get_by_ids(
        self,
        category_ids: list[int] | set[int],
    ) -> dict[int, CategoryEntity]:
        """
        Obtiene múltiples categorías en una sola consulta.

        Retorna un diccionario indexado por ID para permitir
        búsquedas O(1) desde la capa de aplicación.
        """

        normalized_ids = {
            category_id
            for category_id in category_ids
            if isinstance(category_id, int)
            and not isinstance(category_id, bool)
            and category_id > 0
        }

        if not normalized_ids:
            return {}

        models = (
            self.session.query(Category)
            .filter(
                Category.id.in_(normalized_ids)
            )
            .all()
        )

        return {
            model.id: self._to_entity(model)
            for model in models
        }

    def get_by_name(
        self,
        name: str,
    ) -> CategoryEntity | None:

        normalized_name = normalize_category_name(
            name
        )

        model = (
            self.session.query(Category)
            .filter(
                Category.name_normalized
                == normalized_name
            )
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def get_by_slug(
        self,
        slug: str,
    ) -> CategoryEntity | None:
        model = (
            self.session.query(Category)
            .filter(Category.slug == slug)
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def get_active(
        self,
    ) -> list[CategoryEntity]:
        models = (
            self.session.query(Category)
            .filter(Category.is_active == True)
            .order_by(Category.name.asc())
            .all()
        )

        return [
            self._to_entity(model)
            for model in models
        ]

    def get_all(
        self,
    ) -> list[CategoryEntity]:
        models = (
            self.session.query(Category)
            .order_by(Category.name.asc())
            .all()
        )

        return [
            self._to_entity(model)
            for model in models
        ]

    def create(
        self,
        category: CategoryEntity,
    ) -> CategoryEntity:
        model = Category(
            name=category.name,
            slug=category.slug,
            is_active=category.is_active,
        )

        self.session.add(model)

        try:
            self.session.commit()

        except IntegrityError as exc:
            self.session.rollback()

            if is_category_name_integrity_error(
                exc
            ):
                raise DuplicateCategoryNameError(
                    category.name
                ) from exc

            if is_category_slug_integrity_error(
                exc
            ):
                raise DuplicateCategorySlugError(
                    category.slug
                ) from exc

            raise

        return self._to_entity(model)

    def update(
        self,
        category: CategoryEntity,
    ) -> CategoryEntity | None:
        if category.id is None:
            raise ValueError(
                "El ID de la categoría es obligatorio."
            )

        model = self.session.get(
            Category,
            category.id,
        )

        if model is None:
            return None

        model.name = category.name
        model.slug = category.slug
        model.is_active = category.is_active

        try:
            self.session.commit()

        except IntegrityError as exc:
            self.session.rollback()

            if is_category_name_integrity_error(
                exc
            ):
                raise DuplicateCategoryNameError(
                    category.name
                ) from exc

            if is_category_slug_integrity_error(
                exc
            ):
                raise DuplicateCategorySlugError(
                    category.slug
                ) from exc

            raise

        return self._to_entity(model)

    def has_products(
        self,
        category_id: int,
    ) -> bool:
        """Comprueba si existen productos asociados."""

        return (
            self.session.query(Product.id)
            .filter(
                Product.category_id == category_id
            )
            .first()
            is not None
        )

    def delete(
        self,
        category_id: int,
    ) -> CategoryEntity | None:
        model = self.session.get(
            Category,
            category_id,
        )

        if model is None:
            return None

        category = self._to_entity(model)

        self.session.delete(model)
        self.session.commit()

        return category