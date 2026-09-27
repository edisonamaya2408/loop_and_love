from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities.category import CategoryEntity
from app.domain.entities.product import ProductEntity
from app.domain.exceptions import (
    DuplicateCategoryNameError,
    DuplicateCategorySlugError,
    DuplicateProductCodeError,
)
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)


def _unique_suffix():
    return uuid4().hex[:10]


@pytest.fixture
def category_repository(
    app,
    integration_session,
):
    return SQLAlchemyCategoryRepository(
        session=integration_session,
    )


@pytest.fixture
def product_repository(
    app,
    integration_session,
):
    return SQLAlchemyProductRepository(
        session=integration_session,
    )


@pytest.mark.integration
def test_category_repository_rejects_duplicate_name(
    category_repository,
    integration_session,
):
    suffix = _unique_suffix()

    existing = CategoryEntity(
        id=None,
        name=f"Integration Categoria {suffix}",
        slug=f"integration-name-{suffix}",
        is_active=True,
    )

    created = category_repository.create(
        existing
    )

    duplicate = CategoryEntity(
        id=None,
        name=created.name,
        slug=f"integration-other-{suffix}",
        is_active=True,
    )

    try:
        with pytest.raises(
            DuplicateCategoryNameError
        ):
            category_repository.create(
                duplicate
            )

    finally:
        persisted = integration_session.get(
            Category,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_category_repository_rejects_duplicate_slug(
    category_repository,
    integration_session,
):
    suffix = _unique_suffix()

    existing = CategoryEntity(
        id=None,
        name=f"Integration Categoria {suffix}",
        slug=f"integration-slug-{suffix}",
        is_active=True,
    )

    created = category_repository.create(
        existing
    )

    duplicate = CategoryEntity(
        id=None,
        name=f"Integration Otra {suffix}",
        slug=created.slug,
        is_active=True,
    )

    try:
        with pytest.raises(
            DuplicateCategorySlugError
        ):
            category_repository.create(
                duplicate
            )

    finally:
        persisted = integration_session.get(
            Category,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_product_repository_rejects_duplicate_code(
    category_repository,
    product_repository,
    integration_session,
):
    suffix = _unique_suffix()

    category = category_repository.create(
        CategoryEntity(
            id=None,
            name=f"Integration Categoria {suffix}",
            slug=f"integration-product-{suffix}",
            is_active=True,
        )
    )

    code = f"INTEGRATION-{suffix.upper()}"

    existing = ProductEntity(
        id=None,
        code=code,
        name="Producto Integration",
        description="Producto existente.",
        price=Decimal("10000.00"),
        category_id=category.id,
        image_url=None,
        is_active=True,
    )

    created = product_repository.create(
        existing
    )

    duplicate = ProductEntity(
        id=None,
        code=code,
        name="Producto duplicado",
        description="Producto duplicado.",
        price=Decimal("20000.00"),
        category_id=category.id,
        image_url=None,
        is_active=True,
    )

    try:
        with pytest.raises(
            DuplicateProductCodeError
        ):
            product_repository.create(
                duplicate
            )

    finally:
        persisted_product = integration_session.get(
            Product,
            created.id,
        )

        if persisted_product is not None:
            integration_session.delete(
                persisted_product
            )

        persisted_category = integration_session.get(
            Category,
            category.id,
        )

        if persisted_category is not None:
            integration_session.delete(
                persisted_category
            )

        integration_session.commit()