import os

import pytest
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db


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