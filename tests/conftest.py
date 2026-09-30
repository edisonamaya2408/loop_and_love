import os

import pytest

from flask import (
    current_app,
)

from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.presentation.middleware import (
    auth_middleware,
)
from tests.unit.auth_test_helpers import (
    create_isolated_admin_repository,
)


@pytest.fixture(autouse=True)
def isolate_unit_admin_auth(
    request,
    monkeypatch,
):
    """
    Aísla la autenticación administrativa de los unit tests.

    Los unit tests no deben depender del estado persistente
    de admin_users en SQL Server o PostgreSQL.

    Los tests de integración quedan fuera de este mecanismo
    y utilizan el repositorio real.

    Si un test unitario ya inyectó explícitamente un repository
    mediante app.extensions["admin_user_repository"], ese
    repository tiene prioridad.
    """

    is_integration_test = (
        request.node.get_closest_marker(
            "integration"
        )
        is not None
    )

    if is_integration_test:
        return

    def get_admin_user_repository():
        explicit_repository = (
            current_app.extensions.get(
                "admin_user_repository"
            )
        )

        if (
            explicit_repository
            is not None
        ):
            return explicit_repository

        isolated_repository = (
            current_app.extensions.get(
                "_unit_admin_user_repository"
            )
        )

        if (
            isolated_repository
            is None
        ):
            isolated_repository = (
                create_isolated_admin_repository()
            )

            current_app.extensions[
                "_unit_admin_user_repository"
            ] = isolated_repository

        return isolated_repository

    monkeypatch.setattr(
        auth_middleware,
        "_get_admin_user_repository",
        get_admin_user_repository,
    )


@pytest.fixture
def app(request):
    """
    Crea la aplicación correspondiente al tipo de prueba.

    Tests unitarios:
        DevelopmentConfig -> DATABASE_URL

    Tests de integración:
        - Si TEST_DATABASE_URL existe:
            TestingConfig -> TEST_DATABASE_URL
        - Si TEST_DATABASE_URL no existe:
            DevelopmentConfig -> DATABASE_URL

    De esta forma podemos ejecutar toda la suite localmente
    contra SQL Server y, cuando TEST_DATABASE_URL está definida,
    ejecutar la suite de integración contra PostgreSQL.
    """

    is_integration_test = (
        request.node.get_closest_marker(
            "integration"
        )
        is not None
    )

    test_database_url = os.getenv(
        "TEST_DATABASE_URL"
    )

    use_testing_database = (
        is_integration_test
        and bool(test_database_url)
    )

    if use_testing_database:
        environment = "testing"

    else:
        environment = "development"

    app = create_app(
        environment
    )

    if use_testing_database:
        with app.app_context():
            try:
                yield app

            finally:
                db.session.remove()
                db.engine.dispose()

    else:
        try:
            yield app

        finally:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def integration_session(app):
    """
    Sesión SQLAlchemy independiente para pruebas de integración.

    Se utiliza tanto con SQL Server local como con PostgreSQL.
    Los repositories actuales realizan commit(), por lo que
    no utilizamos SAVEPOINT ni una transacción externa.
    """

    session = Session(
        bind=db.engine,
        expire_on_commit=False,
    )

    try:
        yield session

    finally:
        session.rollback()
        session.close()