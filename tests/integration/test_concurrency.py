from concurrent.futures import (
    ThreadPoolExecutor,
)
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.entities.product import (
    ProductEntity,
)
from app.domain.exceptions import (
    DuplicateProductCodeError,
)
from app.extensions import db
from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.repositories.admin_user_repository_impl import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)


def _unique_suffix():
    return uuid4().hex[:12]


def _create_independent_session(engine):
    """
    Crea una sesión completamente independiente de la sesión
    utilizada por el hilo principal del test.

    Nunca compartimos una Session de SQLAlchemy entre hilos.

    El Engine se obtiene en el hilo principal, dentro del contexto
    de Flask del test, y luego se pasa explícitamente a los hilos.
    Esto evita acceder a db.engine desde un hilo sin application context.
    """

    return Session(
        bind=engine,
        expire_on_commit=False,
    )


@pytest.mark.integration
def test_concurrent_product_creation_preserves_unique_code(
    app,
    integration_session,
):
    """
    Dos operaciones concurrentes intentan crear el mismo
    código de producto.

    La unicidad debe ser garantizada por la base de datos:
        - exactamente una operación tiene éxito;
        - exactamente una termina en DuplicateProductCodeError;
        - nunca deben existir dos productos con el mismo código.
    """

    suffix = _unique_suffix()
    engine = db.engine

    category = Category(
        name=(
            f"Concurrency Category "
            f"{suffix}"
        ),
        slug=(
            f"concurrency-category-"
            f"{suffix}"
        ),
        is_active=True,
    )

    integration_session.add(
        category
    )
    integration_session.commit()

    product_code = (
        f"CONCURRENT-{suffix.upper()}"
    )

    barrier = Barrier(2)

    def create_product(
        worker_number,
    ):
        session = (
            _create_independent_session(
                engine
            )
        )

        try:
            repository = (
                SQLAlchemyProductRepository(
                    session=session
                )
            )

            product = ProductEntity(
                id=None,
                code=product_code,
                name=(
                    f"Concurrent Product "
                    f"{worker_number}"
                ),
                description=(
                    "Concurrency test."
                ),
                price=Decimal("10000.00"),
                category_id=category.id,
                image_url=None,
                is_active=True,
            )

            # Ambas operaciones deben llegar al INSERT
            # de forma concurrente.
            barrier.wait(
                timeout=10
            )

            created = repository.create(
                product
            )

            return (
                "success",
                created.id,
                None,
            )

        except DuplicateProductCodeError:
            return (
                "duplicate",
                None,
                None,
            )

        except Exception as error:
            return (
                "unexpected",
                None,
                repr(error),
            )

        finally:
            session.rollback()
            session.close()

    try:
        with ThreadPoolExecutor(
            max_workers=2
        ) as executor:

            futures = [
                executor.submit(
                    create_product,
                    1,
                ),
                executor.submit(
                    create_product,
                    2,
                ),
            ]

            results = [
                future.result(
                    timeout=30
                )
                for future in futures
            ]

        statuses = [
            result[0]
            for result in results
        ]

        assert statuses.count(
            "success"
        ) == 1

        assert statuses.count(
            "duplicate"
        ) == 1

        unexpected_results = [
            result
            for result in results
            if result[0] == "unexpected"
        ]

        assert unexpected_results == []

        persisted_products = (
            integration_session.query(
                Product
            )
            .filter(
                Product.code
                == product_code
            )
            .all()
        )

        assert len(
            persisted_products
        ) == 1

        successful_result = next(
            result
            for result in results
            if result[0] == "success"
        )

        assert (
            persisted_products[0].id
            == successful_result[1]
        )

    finally:
        integration_session.query(
            Product
        ).filter(
            Product.code
            == product_code
        ).delete(
            synchronize_session=False
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


@pytest.mark.integration
def test_concurrent_token_version_increments_are_not_lost(
    app,
    integration_session,
):
    """
    Comprueba que dos incrementos concurrentes de
    token_version no produzcan una actualización perdida.

    Si ambas operaciones parten de 0, el valor final debe ser 2.
    """

    suffix = _unique_suffix()
    engine = db.engine

    repository = (
        SQLAlchemyAdminUserRepository(
            session=integration_session
        )
    )

    admin = repository.create(
        AdminUserEntity(
            id=None,
            email=(
                f"concurrency-admin-"
                f"{suffix}"
                "@loopandlove.test"
            ),
            password_hash="test-hash",
            is_active=True,
            token_version=0,
        )
    )

    barrier = Barrier(2)

    def increment_token_version(
        worker_number,
    ):
        session = (
            _create_independent_session(
                engine
            )
        )

        try:
            worker_repository = (
                SQLAlchemyAdminUserRepository(
                    session=session
                )
            )

            barrier.wait(
                timeout=10
            )

            result = (
                worker_repository.increment_token_version(
                    admin.id
                )
            )

            if result is None:
                return (
                    "missing",
                    None,
                )

            return (
                "success",
                result.token_version,
            )

        except Exception as error:
            return (
                "unexpected",
                repr(error),
            )

        finally:
            session.rollback()
            session.close()

    try:
        with ThreadPoolExecutor(
            max_workers=2
        ) as executor:

            futures = [
                executor.submit(
                    increment_token_version,
                    1,
                ),
                executor.submit(
                    increment_token_version,
                    2,
                ),
            ]

            results = [
                future.result(
                    timeout=30
                )
                for future in futures
            ]

        assert [
            result[0]
            for result in results
        ] == [
            "success",
            "success",
        ]

        integration_session.expire_all()

        persisted_admin = (
            integration_session.get(
                AdminUser,
                admin.id,
            )
        )

        assert persisted_admin is not None

        assert (
            persisted_admin.token_version
            == 2
        )

        returned_versions = {
            result[1]
            for result in results
        }

        assert returned_versions.issubset(
            {1, 2}
        )

    finally:
        persisted_admin = (
            integration_session.get(
                AdminUser,
                admin.id,
            )
        )

        if persisted_admin is not None:
            integration_session.delete(
                persisted_admin
            )

        integration_session.commit()