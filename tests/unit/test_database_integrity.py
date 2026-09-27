from types import SimpleNamespace

from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.integrity import (
    is_product_code_integrity_error,
)


def _integrity_error(
    original_error,
):
    return IntegrityError(
        "INSERT",
        {},
        original_error,
    )


def test_detects_sql_server_product_code_duplicate():
    original_error = SimpleNamespace(
        args=(
            "2601",
            (
                "[SQL Server] Cannot insert duplicate "
                "key row with unique index "
                "'ix_products_code'."
            ),
        )
    )

    error = _integrity_error(
        original_error
    )

    assert (
        is_product_code_integrity_error(error)
        is True
    )


def test_detects_sql_server_alternate_duplicate_key_error():
    original_error = SimpleNamespace(
        args=(
            "2627",
            (
                "[SQL Server] Violation of UNIQUE "
                "KEY constraint 'uq_products_code'."
            ),
        )
    )

    error = _integrity_error(
        original_error
    )

    assert (
        is_product_code_integrity_error(error)
        is True
    )


def test_detects_postgresql_product_code_duplicate():
    original_error = SimpleNamespace(
        sqlstate="23505",
        diag=SimpleNamespace(
            constraint_name="uq_products_code"
        ),
    )

    error = _integrity_error(
        original_error
    )

    assert (
        is_product_code_integrity_error(error)
        is True
    )


def test_rejects_other_postgresql_unique_constraint():
    original_error = SimpleNamespace(
        sqlstate="23505",
        diag=SimpleNamespace(
            constraint_name="uq_products_name"
        ),
    )

    error = _integrity_error(
        original_error
    )

    assert (
        is_product_code_integrity_error(error)
        is False
    )


def test_rejects_other_sql_server_integrity_error():
    original_error = SimpleNamespace(
        args=(
            "547",
            (
                "[SQL Server] The INSERT statement "
                "conflicted with a FOREIGN KEY constraint."
            ),
        )
    )

    error = _integrity_error(
        original_error
    )

    assert (
        is_product_code_integrity_error(error)
        is False
    )


def test_rejects_integrity_error_without_original_error():
    error = IntegrityError(
        "INSERT",
        {},
        None,
    )

    assert (
        is_product_code_integrity_error(error)
        is False
    )