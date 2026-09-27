from decimal import Decimal

from sqlalchemy import (
    func,
    or_,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.product import ProductEntity
from app.domain.exceptions import (
    DuplicateProductCodeError,
)
from app.domain.repositories.product_repository import ProductRepository
from app.extensions import db
from app.infrastructure.database.models.product_model import Product
from app.infrastructure.database.integrity import (
    is_product_code_integrity_error,
)
from app.domain.normalization import (
    normalize_product_code,
)


class SQLAlchemyProductRepository(ProductRepository):
    """Implementación del repositorio de productos usando SQLAlchemy."""

    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(
        model: Product,
    ) -> ProductEntity:
        return ProductEntity(
            id=model.id,
            code=model.code,
            name=model.name,
            description=model.description,
            price=Decimal(str(model.price)),
            category_id=model.category_id,
            image_url=model.image_url,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        model = self.session.get(
            Product,
            product_id,
        )

        if model is None:
            return None

        return self._to_entity(model)

    def get_active_by_id(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        model = (
            self.session.query(Product)
            .filter(
                Product.id == product_id,
                Product.is_active == True,
            )
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    def get_by_code(
        self,
        code: str,
    ) -> ProductEntity | None:

        normalized_code = normalize_product_code(
            code
        )

        model = (
            self.session.query(Product)
            .filter(
                Product.code == normalized_code
            )
            .first()
        )

        if model is None:
            return None

        return self._to_entity(model)

    @staticmethod
    def _count_query(
        query,
    ) -> int:
        """
        Obtiene el total de registros sin utilizar
        Query.count() sobre una subconsulta completa.

        Las consultas actuales no utilizan joins que alteren
        la cardinalidad del producto, por lo que COUNT(id)
        es suficiente.
        """

        total = (
            query
            .order_by(None)
            .with_entities(
                func.count(Product.id)
            )
            .scalar()
        )

        return int(
            total or 0
        )

    def _build_active_query(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ):
        query = (
            self.session.query(Product)
            .filter(Product.is_active == True)
        )

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    Product.name.ilike(
                        search_pattern
                    ),
                    Product.description.ilike(
                        search_pattern
                    ),
                )
            )

        if category_id is not None:
            query = query.filter(
                Product.category_id == category_id
            )

        if min_price is not None:
            query = query.filter(
                Product.price >= min_price
            )

        if max_price is not None:
            query = query.filter(
                Product.price <= max_price
            )

        return query

    def get_active(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> list[ProductEntity]:

        query = self._build_active_query(
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
        )

        query = query.order_by(
            Product.created_at.desc(),
            Product.id.desc(),
        )

        return [
            self._to_entity(model)
            for model in query.all()
        ]

    def get_active_paginated(
        self,
        search: str | None = None,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        offset: int = 0,
        limit: int = 12,
    ) -> tuple[list[ProductEntity], int]:

        query = self._build_active_query(
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
        )

        total = self._count_query(
            query
        )

        models = (
            query
            .order_by(
                Product.created_at.desc(),
                Product.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        products = [
            self._to_entity(model)
            for model in models
        ]

        return products, total

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

        query = self.session.query(Product)

        if search:
            search_pattern = f"%{search}%"

            query = query.filter(
                or_(
                    Product.name.ilike(
                        search_pattern
                    ),
                    Product.description.ilike(
                        search_pattern
                    ),
                    Product.code.ilike(
                        search_pattern
                    ),
                )
            )

        if category_id is not None:
            query = query.filter(
                Product.category_id == category_id
            )

        if min_price is not None:
            query = query.filter(
                Product.price >= min_price
            )

        if max_price is not None:
            query = query.filter(
                Product.price <= max_price
            )

        if is_active is not None:
            query = query.filter(
                Product.is_active == is_active
            )

        total = self._count_query(
            query
        )

        models = (
            query
            .order_by(
                Product.created_at.desc(),
                Product.id.desc(),
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

        products = [
            self._to_entity(model)
            for model in models
        ]

        return products, total

    def get_all(self) -> list[ProductEntity]:
        models = (
            self.session.query(Product)
            .order_by(
                Product.created_at.desc(),
                Product.id.desc(),
            )
            .all()
        )

        return [
            self._to_entity(model)
            for model in models
        ]

    def create(
        self,
        product: ProductEntity,
    ) -> ProductEntity:
        model = Product(
            code=product.code,
            name=product.name,
            description=product.description,
            price=product.price,
            category_id=product.category_id,
            image_url=product.image_url,
            is_active=product.is_active,
        )

        self.session.add(model)

        try:
            self.session.commit()

        except IntegrityError as exc:
            self.session.rollback()

            if is_product_code_integrity_error(
                exc
            ):
                raise DuplicateProductCodeError(
                    product.code
                ) from exc

            raise

        return self._to_entity(model)

    def update(
        self,
        product: ProductEntity,
    ) -> ProductEntity:

        model = self.session.get(
            Product,
            product.id,
        )

        if model is None:
            raise ValueError(
                "El producto no existe."
            )

        model.code = product.code
        model.name = product.name
        model.description = product.description
        model.price = product.price
        model.category_id = product.category_id
        model.image_url = product.image_url
        model.is_active = product.is_active

        try:
            self.session.commit()

        except IntegrityError as exc:
            self.session.rollback()

            if is_product_code_integrity_error(
                exc
            ):
                raise DuplicateProductCodeError(
                    product.code
                ) from exc

            raise

        return self._to_entity(model)

    def delete(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        model = self.session.get(
            Product,
            product_id,
        )

        if model is None:
            return None

        product = self._to_entity(model)

        self.session.delete(model)

        try:
            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return product