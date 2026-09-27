from uuid import uuid4
from decimal import Decimal

import pytest

from app.domain.entities.category import CategoryEntity
from app.extensions import db
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.models.product_model import Product


def _unique_values():
    suffix = uuid4().hex[:10]

    return {
        "name": f"Categoria Test {suffix}",
        "slug": f"categoria-test-{suffix}",
    }


@pytest.fixture
def repository(app):
    with app.app_context():
        yield SQLAlchemyCategoryRepository()


@pytest.fixture
def category(app):
    with app.app_context():
        values = _unique_values()

        category = Category(
            name=values["name"],
            slug=values["slug"],
            is_active=True,
        )

        db.session.add(category)
        db.session.commit()

        yield category

        persisted = db.session.get(
            Category,
            category.id,
        )

        if persisted is not None:
            db.session.delete(persisted)
            db.session.commit()


def test_get_by_id_returns_category(
    repository,
    category,
):
    result = repository.get_by_id(
        category.id
    )

    assert result is not None
    assert result.id == category.id
    assert result.name == category.name
    assert result.slug == category.slug
    assert result.is_active is True


def test_get_by_id_returns_none_when_not_found(
    repository,
):
    result = repository.get_by_id(
        999999999
    )

    assert result is None


def test_get_by_name_returns_category(
    repository,
    category,
):
    result = repository.get_by_name(
        category.name
    )

    assert result is not None
    assert result.id == category.id
    assert result.name == category.name


def test_get_by_name_returns_none_when_not_found(
    repository,
):
    result = repository.get_by_name(
        "Categoria inexistente XYZ"
    )

    assert result is None


def test_get_by_slug_returns_category(
    repository,
    category,
):
    result = repository.get_by_slug(
        category.slug
    )

    assert result is not None
    assert result.id == category.id
    assert result.slug == category.slug


def test_get_by_slug_returns_none_when_not_found(
    repository,
):
    result = repository.get_by_slug(
        "slug-inexistente-xyz"
    )

    assert result is None


def test_get_active_returns_only_active_categories(
    repository,
    app,
):
    with app.app_context():
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

        db.session.add_all(
            [
                active,
                inactive,
            ]
        )
        db.session.commit()

        try:
            result = repository.get_active()

            result_ids = {
                item.id
                for item in result
            }

            assert active.id in result_ids
            assert inactive.id not in result_ids

        finally:
            db.session.delete(active)
            db.session.delete(inactive)
            db.session.commit()


def test_get_all_returns_active_and_inactive_categories(
    repository,
    app,
):
    with app.app_context():
        values_a = _unique_values()
        values_b = _unique_values()

        category_a = Category(
            name=values_a["name"],
            slug=values_a["slug"],
            is_active=True,
        )

        category_b = Category(
            name=values_b["name"],
            slug=values_b["slug"],
            is_active=False,
        )

        db.session.add_all(
            [
                category_a,
                category_b,
            ]
        )
        db.session.commit()

        try:
            result = repository.get_all()

            result_ids = {
                item.id
                for item in result
            }

            assert category_a.id in result_ids
            assert category_b.id in result_ids

        finally:
            db.session.delete(category_a)
            db.session.delete(category_b)
            db.session.commit()


def test_create_persists_category(
    repository,
):
    values = _unique_values()

    category = CategoryEntity(
        id=None,
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

    created = repository.create(
        category
    )

    try:
        assert created.id is not None
        assert created.name == values["name"]
        assert created.slug == values["slug"]
        assert created.is_active is True

        persisted = db.session.get(
            Category,
            created.id,
        )

        assert persisted is not None
        assert persisted.name == values["name"]

    finally:
        persisted = db.session.get(
            Category,
            created.id,
        )

        if persisted is not None:
            db.session.delete(persisted)
            db.session.commit()


def test_update_persists_category(
    repository,
    category,
):
    updated = CategoryEntity(
        id=category.id,
        name=f"{category.name} Actualizada",
        slug=f"{category.slug}-actualizada",
        is_active=False,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )

    result = repository.update(
        updated
    )

    assert result.id == category.id
    assert result.name == updated.name
    assert result.slug == updated.slug
    assert result.is_active is False

    persisted = db.session.get(
        Category,
        category.id,
    )

    assert persisted is not None
    assert persisted.name == updated.name
    assert persisted.slug == updated.slug
    assert persisted.is_active is False


def test_update_returns_none_when_category_does_not_exist(
    repository,
):
    values = _unique_values()

    category = CategoryEntity(
        id=999999999,
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

    result = repository.update(
        category
    )

    assert result is None


def test_update_requires_id(
    repository,
):
    values = _unique_values()

    category = CategoryEntity(
        id=None,
        name=values["name"],
        slug=values["slug"],
        is_active=True,
    )

    with pytest.raises(
        ValueError,
        match="ID de la categoría",
    ):
        repository.update(
            category
        )


def test_delete_returns_deleted_category(
    repository,
    category,
):
    result = repository.delete(
        category.id
    )

    assert result is not None
    assert result.id == category.id
    assert result.name == category.name

    persisted = db.session.get(
        Category,
        category.id,
    )

    assert persisted is None


def test_delete_returns_none_when_category_does_not_exist(
    repository,
):
    result = repository.delete(
        999999999
    )

    assert result is None

def test_has_products_returns_true_when_category_has_product(
    repository,
    app,
):
    with app.app_context():
        values = _unique_values()

        category = Category(
            name=values["name"],
            slug=values["slug"],
            is_active=True,
        )

        db.session.add(category)
        db.session.flush()

        product = Product(
            code=f"TEST-{uuid4().hex[:10].upper()}",
            name="Producto de prueba",
            description=None,
            price=Decimal("10000"),
            category_id=category.id,
            image_url=None,
            is_active=True,
        )

        db.session.add(product)
        db.session.commit()

        try:
            assert repository.has_products(
                category.id
            ) is True

        finally:
            persisted_product = db.session.get(
                Product,
                product.id,
            )

            if persisted_product is not None:
                db.session.delete(
                    persisted_product
                )

            persisted_category = db.session.get(
                Category,
                category.id,
            )

            if persisted_category is not None:
                db.session.delete(
                    persisted_category
                )

            db.session.commit()

def test_has_products_returns_false_when_category_has_no_products(
    repository,
    category,
):
    assert repository.has_products(
        category.id
    ) is False