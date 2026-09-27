import pytest
from sqlalchemy import inspect, text

from app.domain.entities.category import (
    CategoryEntity,
)
from app.domain.entities.product import (
    ProductEntity,
)
from app.extensions import db
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


def _require_postgresql(app):
    if db.engine.dialect.name != "postgresql":
        pytest.skip(
            "TEST_DATABASE_URL no apunta a PostgreSQL."
        )


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_connection(
    app,
):
    with app.app_context():
        _require_postgresql(app)

        result = db.session.execute(
            text("SELECT 1")
        ).scalar_one()

        assert result == 1


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_required_schema(
    app,
):
    with app.app_context():
        _require_postgresql(app)

        inspector = inspect(
            db.engine
        )

        tables = set(
            inspector.get_table_names()
        )

        assert {
            "admin_users",
            "categories",
            "products",
        }.issubset(tables)


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_category_schema(
    app,
):
    with app.app_context():
        _require_postgresql(app)

        inspector = inspect(
            db.engine
        )

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "categories"
            )
        }

        assert {
            "id",
            "name",
            "name_normalized",
            "slug",
            "is_active",
            "created_at",
            "updated_at",
        }.issubset(columns)

        constraints = {
            constraint["name"]
            for constraint
            in inspector.get_unique_constraints(
                "categories"
            )
            if constraint.get("name")
        }

        assert (
            "uq_categories_name_normalized"
            in constraints
        )

        assert (
            "uq_categories_slug"
            in constraints
        )


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_product_schema(
    app,
):
    with app.app_context():
        _require_postgresql(app)

        inspector = inspect(
            db.engine
        )

        constraints = {
            constraint["name"]
            for constraint
            in inspector.get_unique_constraints(
                "products"
            )
            if constraint.get("name")
        }

        assert (
            "uq_products_code"
            in constraints
        )


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_unicode_persistence(
    app,
    integration_session,
):
    with app.app_context():
        _require_postgresql(app)

        repository = (
            SQLAlchemyCategoryRepository(
                session=integration_session,
            )
        )

        category = repository.create(
            CategoryEntity(
                id=None,
                name="Amigurumís Ñandú Ángel",
                slug=(
                    "amigurumis-nandu-angel-"
                    "postgresql"
                ),
                is_active=True,
            )
        )

        try:
            integration_session.expire_all()

            persisted = (
                integration_session.get(
                    Category,
                    category.id,
                )
            )

            assert persisted is not None

            assert (
                persisted.name
                == "Amigurumís Ñandú Ángel"
            )

            assert (
                persisted.name_normalized
                == "amigurumís ñandú ángel"
            )

        finally:
            persisted = (
                integration_session.get(
                    Category,
                    category.id,
                )
            )

            if persisted is not None:
                integration_session.delete(
                    persisted
                )
                integration_session.commit()


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_canonical_category_lookup(
    app,
    integration_session,
):
    with app.app_context():
        _require_postgresql(app)

        repository = (
            SQLAlchemyCategoryRepository(
                session=integration_session,
            )
        )

        category = repository.create(
            CategoryEntity(
                id=None,
                name="Amigurumis Crochet",
                slug=(
                    "amigurumis-crochet-"
                    "postgresql"
                ),
                is_active=True,
            )
        )

        try:
            found = repository.get_by_name(
                "  AMIGURUMIS   CROCHET "
            )

            assert found is not None
            assert found.id == category.id

        finally:
            persisted = (
                integration_session.get(
                    Category,
                    category.id,
                )
            )

            if persisted is not None:
                integration_session.delete(
                    persisted
                )
                integration_session.commit()


@pytest.mark.integration
@pytest.mark.postgresql
def test_postgresql_canonical_product_code(
    app,
    integration_session,
):
    with app.app_context():
        _require_postgresql(app)

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

        category = (
            category_repository.create(
                CategoryEntity(
                    id=None,
                    name=(
                        "PostgreSQL Product Test"
                    ),
                    slug=(
                        "postgresql-product-test"
                    ),
                    is_active=True,
                )
            )
        )

        product = None

        try:
            product = (
                product_repository.create(
                    ProductEntity(
                        id=None,
                        code="  oso-pg-001 ",
                        name="Producto PostgreSQL",
                        description=None,
                        price=90000,
                        category_id=category.id,
                        image_url=None,
                        is_active=True,
                    )
                )
            )

            assert (
                product.code
                == "OSO-PG-001"
            )

            found = (
                product_repository.get_by_code(
                    "oso-pg-001"
                )
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