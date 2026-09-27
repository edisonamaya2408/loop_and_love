from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities.category import CategoryEntity
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)


def _unique_values():
    suffix = uuid4().hex[:10]

    return {
        "name": f"Integration Categoria {suffix}",
        "slug": f"integration-categoria-{suffix}",
    }


@pytest.fixture
def repository(
    integration_session,
):
    yield SQLAlchemyCategoryRepository(
        session=integration_session
    )


@pytest.fixture
def persisted_category(
    integration_session,
):
    values = _unique_values()

    category = Category(
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

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


@pytest.mark.integration
def test_category_repository_get_by_id(
    repository,
    persisted_category,
):
    result = repository.get_by_id(
        persisted_category.id
    )

    assert result is not None
    assert result.id == persisted_category.id
    assert result.name == persisted_category.name
    assert result.slug == persisted_category.slug
    assert result.is_active is True


@pytest.mark.integration
def test_category_repository_create(
    repository,
):
    values = _unique_values()

    category = CategoryEntity(
        id=None,
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

    created = repository.create(category)

    try:
        assert created.id is not None
        assert created.name == values["name"]
        assert created.slug == values["slug"]
        assert created.is_active is True

        persisted = repository.session.get(
            Category,
            created.id,
        )

        assert persisted is not None
        assert persisted.name == values["name"]
        assert persisted.slug == values["slug"]

    finally:
        persisted = repository.session.get(
            Category,
            created.id,
        )

        if persisted is not None:
            repository.session.delete(
                persisted
            )
            repository.session.commit()


@pytest.mark.integration
def test_category_repository_update(
    repository,
    persisted_category,
):
    updated = CategoryEntity(
        id=persisted_category.id,
        name=(
            f"{persisted_category.name} Updated"
        ),
        slug=(
            f"{persisted_category.slug}-updated"
        ),
        is_active=False,
        created_at=(
            persisted_category.created_at
        ),
        updated_at=(
            persisted_category.updated_at
        ),
    )

    result = repository.update(updated)

    assert result is not None
    assert result.id == persisted_category.id
    assert result.name == updated.name
    assert result.slug == updated.slug
    assert result.is_active is False

    persisted = repository.session.get(
        Category,
        persisted_category.id,
    )

    assert persisted is not None
    assert persisted.name == updated.name
    assert persisted.slug == updated.slug
    assert persisted.is_active is False


@pytest.mark.integration
def test_category_repository_get_active_excludes_inactive(
    repository,
    integration_session,
):
    active_values = _unique_values()
    inactive_values = _unique_values()

    active = Category(
        name=active_values["name"],
        slug=active_values["slug"],
        is_active=True,
    )

    inactive = Category(
        name=inactive_values["name"],
        slug=inactive_values["slug"],
        is_active=False,
    )

    integration_session.add_all(
        [
            active,
            inactive,
        ]
    )
    integration_session.commit()

    try:
        result = repository.get_active()

        result_ids = {
            item.id
            for item in result
        }

        assert active.id in result_ids
        assert inactive.id not in result_ids

    finally:
        persisted_active = integration_session.get(
            Category,
            active.id,
        )

        persisted_inactive = integration_session.get(
            Category,
            inactive.id,
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
def test_category_repository_has_products(
    repository,
    integration_session,
):
    values = _unique_values()

    category = Category(
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

    integration_session.add(category)
    integration_session.flush()

    product = Product(
        code=(
            f"INTEGRATION-"
            f"{uuid4().hex[:10].upper()}"
        ),
        name="Producto Integration",
        description=None,
        price=Decimal("10000"),
        category_id=category.id,
        image_url=None,
        is_active=True,
    )

    integration_session.add(product)
    integration_session.commit()

    try:
        assert (
            repository.has_products(
                category.id
            )
            is True
        )

    finally:
        persisted_product = integration_session.get(
            Product,
            product.id,
        )

        persisted_category = integration_session.get(
            Category,
            category.id,
        )

        if persisted_product is not None:
            integration_session.delete(
                persisted_product
            )

        if persisted_category is not None:
            integration_session.delete(
                persisted_category
            )

        integration_session.commit()