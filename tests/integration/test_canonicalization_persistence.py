import pytest

from app.domain.entities.category import (
    CategoryEntity,
)
from app.domain.exceptions import (
    DuplicateCategoryNameError,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)


@pytest.mark.integration
def test_category_name_lookup_is_case_insensitive_and_portable(
    app,
    integration_session,
):
    repository = SQLAlchemyCategoryRepository(
        session=integration_session,
    )

    category = repository.create(
        CategoryEntity(
            id=None,
            name="Amigurumis Crochet",
            slug="amigurumis-crochet",
            is_active=True,
        )
    )

    try:
        found = repository.get_by_name(
            "  AMIGURUMIS   CROCHET "
        )

        assert found is not None
        assert found.id == category.id

        with pytest.raises(
            DuplicateCategoryNameError
        ):
            repository.create(
                CategoryEntity(
                    id=None,
                    name="AMIGURUMIS CROCHET",
                    slug="otra-categoria",
                    is_active=True,
                )
            )

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
def test_product_code_is_canonicalized_before_persistence(
    app,
    integration_session,
):
    category_repository = (
        SQLAlchemyCategoryRepository(
            session=integration_session,
        )
    )

    product_repository = (
        SQLAlchemyProductRepository(
            session=integration_session,
        )
    )

    category = category_repository.create(
        CategoryEntity(
            id=None,
            name="Canonicalization Test",
            slug="canonicalization-test",
            is_active=True,
        )
    )

    product = None

    try:
        from app.domain.entities.product import (
            ProductEntity,
        )

        product = product_repository.create(
            ProductEntity(
                id=None,
                code="  oso-001 ",
                name="Producto Oso",
                description=None,
                price=90000,
                category_id=category.id,
                image_url=None,
                is_active=True,
            )
        )

        assert product.code == "OSO-001"

        found = product_repository.get_by_code(
            "oso-001"
        )

        assert found is not None
        assert found.id == product.id

    finally:
        if product is not None:
            persisted_product = (
                integration_session.get(
                    Product,
                    product.id,
                )
            )

            if persisted_product is not None:
                integration_session.delete(
                    persisted_product
                )

        persisted_category = (
            integration_session.get(
                Category,
                category.id,
            )
        )

        if persisted_category is not None:
            integration_session.delete(
                persisted_category
            )

        integration_session.commit()