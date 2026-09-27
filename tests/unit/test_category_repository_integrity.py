from uuid import uuid4

import pytest

from app.domain.entities.category import CategoryEntity
from app.domain.exceptions import (
    DuplicateCategoryNameError,
    DuplicateCategorySlugError,
)
from app.extensions import db
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)


@pytest.fixture
def repository(app):
    with app.app_context():
        yield SQLAlchemyCategoryRepository()


def _unique_values():
    suffix = uuid4().hex[:10]

    return {
        "name": f"Categoria {suffix}",
        "slug": f"categoria-{suffix}",
    }


def test_create_raises_duplicate_category_name(
    repository,
    app,
):
    with app.app_context():
        values = _unique_values()

        existing = Category(
            name=values["name"],
            slug=values["slug"],
            is_active=True,
        )

        db.session.add(existing)
        db.session.commit()

        try:
            duplicate = CategoryEntity(
                id=None,
                name=values["name"],
                slug=f"{values['slug']}-otro",
                is_active=True,
            )

            with pytest.raises(
                DuplicateCategoryNameError
            ):
                repository.create(
                    duplicate
                )

        finally:
            persisted = db.session.get(
                Category,
                existing.id,
            )

            if persisted is not None:
                db.session.delete(
                    persisted
                )

            db.session.commit()


def test_create_raises_duplicate_category_slug(
    repository,
    app,
):
    with app.app_context():
        values = _unique_values()

        existing = Category(
            name=values["name"],
            slug=values["slug"],
            is_active=True,
        )

        db.session.add(existing)
        db.session.commit()

        try:
            duplicate = CategoryEntity(
                id=None,
                name=f"{values['name']} 2",
                slug=values["slug"],
                is_active=True,
            )

            with pytest.raises(
                DuplicateCategorySlugError
            ):
                repository.create(
                    duplicate
                )

        finally:
            persisted = db.session.get(
                Category,
                existing.id,
            )

            if persisted is not None:
                db.session.delete(
                    persisted
                )

            db.session.commit()