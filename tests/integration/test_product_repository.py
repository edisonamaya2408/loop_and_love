from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities.product import ProductEntity
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)


def _unique_suffix():
    return uuid4().hex[:10]


def _create_category():
    suffix = _unique_suffix()

    return Category(
        name=f"Integration Categoria {suffix}",
        slug=f"integration-categoria-{suffix}",
        is_active=True,
    )


def _create_product(
    category_id,
    *,
    active=True,
    name=None,
    code=None,
    price="10000",
):
    suffix = _unique_suffix()

    return Product(
        code=code
        or f"INTEGRATION-{suffix.upper()}",
        name=name
        or f"Producto Integration {suffix}",
        description=(
            "Producto de prueba de integración."
        ),
        price=Decimal(price),
        category_id=category_id,
        image_url=None,
        is_active=active,
    )


@pytest.fixture
def repository(
    integration_session,
):
    yield SQLAlchemyProductRepository(
        session=integration_session
    )


@pytest.fixture
def persisted_category(
    integration_session,
):
    category = _create_category()

    integration_session.add(category)
    integration_session.commit()

    try:
        yield category

    finally:
        persisted = integration_session.get(
            Category,
            category.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.fixture
def persisted_product(
    integration_session,
    persisted_category,
):
    product = _create_product(
        persisted_category.id
    )

    integration_session.add(product)
    integration_session.commit()

    try:
        yield product

    finally:
        persisted = integration_session.get(
            Product,
            product.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_product_repository_get_by_id(
    repository,
    persisted_product,
):
    result = repository.get_by_id(
        persisted_product.id
    )

    assert result is not None
    assert result.id == persisted_product.id
    assert result.code == persisted_product.code
    assert result.name == persisted_product.name
    assert result.category_id == (
        persisted_product.category_id
    )
    assert result.price == Decimal("10000.00")


@pytest.mark.integration
def test_product_repository_get_by_code(
    repository,
    persisted_product,
):
    result = repository.get_by_code(
        persisted_product.code
    )

    assert result is not None
    assert result.id == persisted_product.id
    assert result.code == persisted_product.code


@pytest.mark.integration
def test_product_repository_get_active_by_id(
    repository,
    persisted_product,
):
    result = repository.get_active_by_id(
        persisted_product.id
    )

    assert result is not None
    assert result.id == persisted_product.id
    assert result.is_active is True


@pytest.mark.integration
def test_product_repository_get_active_excludes_inactive(
    repository,
    integration_session,
    persisted_category,
):
    active_product = _create_product(
        persisted_category.id,
        active=True,
        name=(
            f"Producto Activo "
            f"{_unique_suffix()}"
        ),
    )

    inactive_product = _create_product(
        persisted_category.id,
        active=False,
        name=(
            f"Producto Inactivo "
            f"{_unique_suffix()}"
        ),
    )

    integration_session.add_all(
        [
            active_product,
            inactive_product,
        ]
    )

    integration_session.commit()

    try:
        results = repository.get_active()

        result_ids = {
            product.id
            for product in results
        }

        assert active_product.id in result_ids
        assert inactive_product.id not in result_ids

    finally:
        persisted_active = integration_session.get(
            Product,
            active_product.id,
        )

        persisted_inactive = integration_session.get(
            Product,
            inactive_product.id,
        )

        if persisted_active is not None:
            integration_session.delete(
                persisted_active
            )

        if persisted_inactive is not None:
            integration_session.delete(
                persisted_inactive
            )

        integration_session.commit()


@pytest.mark.integration
def test_product_repository_filters_by_category(
    repository,
    integration_session,
    persisted_category,
):
    second_category = _create_category()

    integration_session.add(
        second_category
    )
    integration_session.flush()

    first_product = _create_product(
        persisted_category.id,
        name=(
            f"Producto Categoria A "
            f"{_unique_suffix()}"
        ),
    )

    second_product = _create_product(
        second_category.id,
        name=(
            f"Producto Categoria B "
            f"{_unique_suffix()}"
        ),
    )

    integration_session.add_all(
        [
            first_product,
            second_product,
        ]
    )

    integration_session.commit()

    try:
        results = repository.get_active(
            category_id=persisted_category.id
        )

        result_ids = {
            product.id
            for product in results
        }

        assert first_product.id in result_ids
        assert second_product.id not in result_ids

    finally:
        persisted_first = integration_session.get(
            Product,
            first_product.id,
        )

        persisted_second = integration_session.get(
            Product,
            second_product.id,
        )

        persisted_second_category = (
            integration_session.get(
                Category,
                second_category.id,
            )
        )

        if persisted_first is not None:
            integration_session.delete(
                persisted_first
            )

        if persisted_second is not None:
            integration_session.delete(
                persisted_second
            )

        if persisted_second_category is not None:
            integration_session.delete(
                persisted_second_category
            )

        integration_session.commit()


@pytest.mark.integration
def test_product_repository_searches_name(
    repository,
    integration_session,
    persisted_category,
):
    product = _create_product(
        persisted_category.id,
        name=(
            "Amigurumi Integration "
            f"{_unique_suffix()}"
        ),
    )

    integration_session.add(product)
    integration_session.commit()

    try:
        results = repository.get_active(
            search="Amigurumi Integration",
        )

        result_ids = {
            item.id
            for item in results
        }

        assert product.id in result_ids

    finally:
        persisted = integration_session.get(
            Product,
            product.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_product_repository_get_active_paginated(
    repository,
    integration_session,
    persisted_category,
):
    products = [
        _create_product(
            persisted_category.id,
            name=(
                f"Producto Paginado "
                f"{_unique_suffix()}"
            ),
            price="10000",
        ),
        _create_product(
            persisted_category.id,
            name=(
                f"Producto Paginado "
                f"{_unique_suffix()}"
            ),
            price="20000",
        ),
        _create_product(
            persisted_category.id,
            name=(
                f"Producto Paginado "
                f"{_unique_suffix()}"
            ),
            price="30000",
        ),
    ]

    integration_session.add_all(products)
    integration_session.commit()

    try:
        result, total = (
            repository.get_active_paginated(
                category_id=(
                    persisted_category.id
                ),
                offset=0,
                limit=2,
            )
        )

        result_ids = {
            product.id
            for product in result
        }

        expected_ids = {
            product.id
            for product in products
        }

        assert total >= 3
        assert len(result) == 2
        assert result_ids.issubset(
            expected_ids
        )

    finally:
        for product in products:
            persisted = integration_session.get(
                Product,
                product.id,
            )

            if persisted is not None:
                integration_session.delete(
                    persisted
                )

        integration_session.commit()


@pytest.mark.integration
def test_product_repository_get_all_paginated_filters_status(
    repository,
    integration_session,
    persisted_category,
):
    active_product = _create_product(
        persisted_category.id,
        active=True,
        name=(
            f"Producto Active "
            f"{_unique_suffix()}"
        ),
    )

    inactive_product = _create_product(
        persisted_category.id,
        active=False,
        name=(
            f"Producto Inactive "
            f"{_unique_suffix()}"
        ),
    )

    integration_session.add_all(
        [
            active_product,
            inactive_product,
        ]
    )

    integration_session.commit()

    try:
        (
            active_results,
            active_total,
        ) = repository.get_all_paginated(
            category_id=(
                persisted_category.id
            ),
            is_active=True,
        )

        active_ids = {
            product.id
            for product in active_results
        }

        assert active_product.id in active_ids
        assert inactive_product.id not in (
            active_ids
        )
        assert active_total >= 1

        (
            inactive_results,
            inactive_total,
        ) = repository.get_all_paginated(
            category_id=(
                persisted_category.id
            ),
            is_active=False,
        )

        inactive_ids = {
            product.id
            for product in inactive_results
        }

        assert inactive_product.id in (
            inactive_ids
        )
        assert active_product.id not in (
            inactive_ids
        )
        assert inactive_total >= 1

    finally:
        persisted_active = integration_session.get(
            Product,
            active_product.id,
        )

        persisted_inactive = integration_session.get(
            Product,
            inactive_product.id,
        )

        if persisted_active is not None:
            integration_session.delete(
                persisted_active
            )

        if persisted_inactive is not None:
            integration_session.delete(
                persisted_inactive
            )

        integration_session.commit()


@pytest.mark.integration
def test_product_repository_create(
    repository,
    persisted_category,
):
    product = ProductEntity(
        id=None,
        code=(
            f"INTEGRATION-"
            f"{_unique_suffix().upper()}"
        ),
        name="Producto creado Integration",
        description="Descripción de integración.",
        price=Decimal("12500.50"),
        category_id=persisted_category.id,
        image_url=None,
        is_active=True,
    )

    created = repository.create(product)

    try:
        assert created.id is not None
        assert created.code == product.code
        assert created.name == product.name
        assert created.price == Decimal("12500.50")
        assert created.category_id == (
            persisted_category.id
        )

        persisted = repository.session.get(
            Product,
            created.id,
        )

        assert persisted is not None
        assert persisted.code == product.code
        assert persisted.category_id == (
            persisted_category.id
        )

    finally:
        persisted = repository.session.get(
            Product,
            created.id,
        )

        if persisted is not None:
            repository.session.delete(
                persisted
            )
            repository.session.commit()


@pytest.mark.integration
def test_product_repository_update(
    repository,
    persisted_product,
):
    updated = ProductEntity(
        id=persisted_product.id,
        code=persisted_product.code,
        name="Producto actualizado Integration",
        description="Descripción actualizada.",
        price=Decimal("18000.75"),
        category_id=(
            persisted_product.category_id
        ),
        image_url=None,
        is_active=False,
        created_at=(
            persisted_product.created_at
        ),
        updated_at=(
            persisted_product.updated_at
        ),
    )

    result = repository.update(updated)

    assert result.id == persisted_product.id
    assert result.name == updated.name
    assert result.price == Decimal("18000.75")
    assert result.is_active is False

    persisted = repository.session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None
    assert persisted.name == updated.name
    assert persisted.price == Decimal("18000.75")
    assert persisted.is_active is False


@pytest.mark.integration
def test_product_repository_delete(
    repository,
    integration_session,
    persisted_category,
):
    product = _create_product(
        persisted_category.id
    )

    integration_session.add(product)
    integration_session.commit()

    product_id = product.id

    deleted = repository.delete(
        product_id
    )

    assert deleted is not None
    assert deleted.id == product_id
    assert deleted.code == product.code

    persisted = repository.session.get(
        Product,
        product_id,
    )

    assert persisted is None

@pytest.mark.integration
def test_product_repository_pagination_has_deterministic_order(
    repository,
    integration_session,
    persisted_category,
):
    created_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    first_product = _create_product(
        persisted_category.id,
        name="Producto Orden 1",
        price="10000",
    )

    second_product = _create_product(
        persisted_category.id,
        name="Producto Orden 2",
        price="20000",
    )

    first_product.created_at = (
        created_at
    )

    second_product.created_at = (
        created_at
    )

    integration_session.add_all(
        [
            first_product,
            second_product,
        ]
    )

    integration_session.commit()

    try:
        result, total = (
            repository.get_active_paginated(
                category_id=(
                    persisted_category.id
                ),
                offset=0,
                limit=2,
            )
        )

        assert total >= 2

        result_ids = [
            product.id
            for product in result
            if product.id
            in {
                first_product.id,
                second_product.id,
            }
        ]

        assert result_ids == [
            max(
                first_product.id,
                second_product.id,
            ),
            min(
                first_product.id,
                second_product.id,
            ),
        ]

    finally:
        persisted_first = (
            integration_session.get(
                Product,
                first_product.id,
            )
        )

        persisted_second = (
            integration_session.get(
                Product,
                second_product.id,
            )
        )

        if persisted_first is not None:
            integration_session.delete(
                persisted_first
            )

        if persisted_second is not None:
            integration_session.delete(
                persisted_second
            )

        integration_session.commit()