from sqlalchemy.exc import IntegrityError


PRODUCT_CODE_UNIQUE_INDEX = "ix_products_code"
PRODUCT_CODE_UNIQUE_CONSTRAINT = "uq_products_code"

POSTGRES_UNIQUE_VIOLATION = "23505"

SQL_SERVER_DUPLICATE_KEY_ERRORS = {
    "2601",
    "2627",
}

CATEGORY_NAME_UNIQUE_CONSTRAINT = (
    "uq_categories_name_normalized"
)

LEGACY_CATEGORY_NAME_UNIQUE_CONSTRAINT = (
    "uq_categories_name"
)

CATEGORY_SLUG_UNIQUE_CONSTRAINT = (
    "uq_categories_slug"
)


def _get_original_error(
    error: IntegrityError,
):
    return getattr(
        error,
        "orig",
        None,
    )


def _get_error_arguments(
    original_error,
) -> tuple:
    args = getattr(
        original_error,
        "args",
        (),
    )

    if not args:
        return ()

    return tuple(
        str(argument)
        for argument in args
    )


def _is_postgres_unique_violation(
    original_error,
) -> bool:
    sqlstate = getattr(
        original_error,
        "sqlstate",
        None,
    )

    if sqlstate is None:
        sqlstate = getattr(
            original_error,
            "pgcode",
            None,
        )

    return sqlstate == POSTGRES_UNIQUE_VIOLATION


def _is_sql_server_duplicate_key(
    original_error,
) -> bool:
    """
    Detecta errores de clave duplicada de SQL Server
    cuando se utiliza pyodbc.

    pyodbc puede representar el error de dos formas:

    1. Código directamente en args[0]:
       ("2601", "...")

    2. SQLSTATE en args[0] y código SQL Server dentro
       del mensaje:
       ("23000", "... (2627) ...")
    """

    arguments = _get_error_arguments(
        original_error
    )

    if not arguments:
        return False

    if arguments[0] in SQL_SERVER_DUPLICATE_KEY_ERRORS:
        return True

    message = " ".join(
        arguments
    )

    return any(
        f"({error_code})" in message
        for error_code in SQL_SERVER_DUPLICATE_KEY_ERRORS
    )


def _contains_product_code_identifier(
    original_error,
) -> bool:
    constraint_name = getattr(
        getattr(
            original_error,
            "diag",
            None,
        ),
        "constraint_name",
        None,
    )

    if constraint_name in (
        PRODUCT_CODE_UNIQUE_CONSTRAINT,
        PRODUCT_CODE_UNIQUE_INDEX,
    ):
        return True

    message = " ".join(
        _get_error_arguments(
            original_error
        )
    ).lower()

    return (
        PRODUCT_CODE_UNIQUE_INDEX.lower()
        in message
        or PRODUCT_CODE_UNIQUE_CONSTRAINT.lower()
        in message
    )


def is_product_code_integrity_error(
    error: IntegrityError,
) -> bool:
    """
    Determina si un IntegrityError corresponde
    exclusivamente a la unicidad del código de producto.

    Soporta los formatos utilizados por:
    - SQL Server + pyodbc
    - PostgreSQL + psycopg
    """

    original_error = _get_original_error(
        error
    )

    if original_error is None:
        return False

    if _is_postgres_unique_violation(
        original_error
    ):
        return _contains_product_code_identifier(
            original_error
        )

    if _is_sql_server_duplicate_key(
        original_error
    ):
        return _contains_product_code_identifier(
            original_error
        )

    return False

def _contains_category_identifier(
    original_error,
    identifier: str,
) -> bool:
    constraint_name = getattr(
        getattr(
            original_error,
            "diag",
            None,
        ),
        "constraint_name",
        None,
    )

    if constraint_name == identifier:
        return True

    message = " ".join(
        _get_error_arguments(
            original_error
        )
    ).lower()

    return identifier.lower() in message

def is_category_name_integrity_error(
    error: IntegrityError,
) -> bool:
    """
    Determina si el IntegrityError corresponde
    a la unicidad del nombre de categoría.
    """

    original_error = _get_original_error(
        error
    )

    if original_error is None:
        return False

    if _is_postgres_unique_violation(
        original_error
    ):
        return (
            _contains_category_identifier(
                original_error,
                CATEGORY_NAME_UNIQUE_CONSTRAINT,
            )
            or _contains_category_identifier(
                original_error,
                LEGACY_CATEGORY_NAME_UNIQUE_CONSTRAINT,
            )
        )

    if _is_sql_server_duplicate_key(
        original_error
    ):
        return _contains_category_identifier(
            original_error,
            CATEGORY_NAME_UNIQUE_CONSTRAINT,
        )

    return False

def is_category_slug_integrity_error(
    error: IntegrityError,
) -> bool:
    """
    Determina si el IntegrityError corresponde
    a la unicidad del slug de categoría.
    """

    original_error = _get_original_error(
        error
    )

    if original_error is None:
        return False

    if _is_postgres_unique_violation(
        original_error
    ):
        return _contains_category_identifier(
            original_error,
            CATEGORY_SLUG_UNIQUE_CONSTRAINT,
        )

    if _is_sql_server_duplicate_key(
        original_error
    ):
        return _contains_category_identifier(
            original_error,
            CATEGORY_SLUG_UNIQUE_CONSTRAINT,
        )

    return False