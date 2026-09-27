from sqlalchemy.dialects import mssql
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)


def _compile_table(table, dialect):
    return str(
        CreateTable(table).compile(
            dialect=dialect,
        )
    ).upper()


def test_admin_user_compiles_for_sql_server():
    sql = _compile_table(
        AdminUser.__table__,
        mssql.dialect(),
    )

    assert "NVARCHAR(255)" in sql
    assert "DATETIME" in sql


def test_admin_user_compiles_for_postgresql():
    sql = _compile_table(
        AdminUser.__table__,
        postgresql.dialect(),
    )

    assert "VARCHAR(255)" in sql
    assert "TIMESTAMP" in sql


def test_category_compiles_for_sql_server():
    sql = _compile_table(
        Category.__table__,
        mssql.dialect(),
    )

    assert "NVARCHAR(100)" in sql
    assert "DATETIME" in sql


def test_category_compiles_for_postgresql():
    sql = _compile_table(
        Category.__table__,
        postgresql.dialect(),
    )

    assert "VARCHAR(100)" in sql
    assert "TIMESTAMP" in sql


def test_product_compiles_for_sql_server():
    sql = _compile_table(
        Product.__table__,
        mssql.dialect(),
    )

    assert "NVARCHAR(50)" in sql
    assert "NVARCHAR(150)" in sql

    # UnicodeText es un tipo portable.
    # Según la configuración/version del dialecto MSSQL
    # puede representarse como NTEXT o NVARCHAR(MAX).
    assert (
        "NTEXT" in sql
        or "NVARCHAR(MAX)" in sql
    )


def test_product_compiles_for_postgresql():
    sql = _compile_table(
        Product.__table__,
        postgresql.dialect(),
    )

    assert "VARCHAR(50)" in sql
    assert "VARCHAR(150)" in sql
    assert "TEXT" in sql

def test_product_code_has_expected_unique_constraint():
    constraints = {
        constraint.name
        for constraint in Product.__table__.constraints
        if constraint.name is not None
    }

    assert "uq_products_code" in constraints