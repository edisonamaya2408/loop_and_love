"""canonicalize business keys

Revision ID: c31d5e8f2a77
Revises: 7f2c1a9d4e61
Create Date: 2026-09-17
"""

import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "c31d5e8f2a77"
down_revision = "7f2c1a9d4e61"
branch_labels = None
depends_on = None


def _normalize_email(value):
    if value is None:
        return None

    value = unicodedata.normalize(
        "NFKC",
        str(value),
    )

    return value.strip().lower()


def _normalize_product_code(value):
    if value is None:
        return None

    value = unicodedata.normalize(
        "NFKC",
        str(value),
    )

    return value.strip().upper()


def _normalize_category_display_name(value):
    if value is None:
        return None

    value = unicodedata.normalize(
        "NFKC",
        str(value),
    )

    return " ".join(
        value.strip().split()
    )


def _normalize_category_name(value):
    display_name = (
        _normalize_category_display_name(
            value
        )
    )

    if not display_name:
        return None

    return display_name.casefold()


def _validate_no_duplicates(
    rows,
    normalizer,
    description,
):
    seen = {}

    for row in rows:
        normalized = normalizer(
            row[1]
        )

        if normalized is None:
            raise RuntimeError(
                f"No se puede normalizar {description}: "
                f"el registro id={row[0]} tiene un valor vacío o nulo."
            )

        if normalized in seen:
            raise RuntimeError(
                f"No se puede aplicar la canonicalización de "
                f"{description}: los registros "
                f"id={seen[normalized]} y id={row[0]} "
                f"producirían el mismo valor canónico "
                f"'{normalized}'. Corrija los datos antes "
                f"de ejecutar esta migración."
            )

        seen[normalized] = row[0]

    return seen


def upgrade():
    bind = op.get_bind()

    # =========================================================
    # 1. Admin user emails
    # =========================================================

    admin_users = sa.table(
        "admin_users",
        sa.column("id", sa.Integer()),
        sa.column("email", sa.Unicode(255)),
    )

    email_rows = bind.execute(
        sa.select(
            admin_users.c.id,
            admin_users.c.email,
        )
        .order_by(admin_users.c.id)
    ).fetchall()

    _validate_no_duplicates(
        email_rows,
        _normalize_email,
        "los correos electrónicos",
    )

    for row in email_rows:
        normalized_email = _normalize_email(
            row.email
        )

        if len(normalized_email) > 255:
            raise RuntimeError(
                "El correo electrónico normalizado "
                f"del usuario id={row.id} supera "
                "los 255 caracteres."
            )

        bind.execute(
            admin_users.update()
            .where(
                admin_users.c.id == row.id
            )
            .values(
                email=normalized_email
            )
        )

    # =========================================================
    # 2. Product codes
    # =========================================================

    products = sa.table(
        "products",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.Unicode(50)),
    )

    product_rows = bind.execute(
        sa.select(
            products.c.id,
            products.c.code,
        )
        .order_by(products.c.id)
    ).fetchall()

    _validate_no_duplicates(
        product_rows,
        _normalize_product_code,
        "los códigos de producto",
    )

    for row in product_rows:
        normalized_code = (
            _normalize_product_code(
                row.code
            )
        )

        if len(normalized_code) > 50:
            raise RuntimeError(
                "El código de producto normalizado "
                f"del producto id={row.id} "
                "supera los 50 caracteres."
            )

        bind.execute(
            products.update()
            .where(
                products.c.id == row.id
            )
            .values(
                code=normalized_code
            )
        )

    # =========================================================
    # 3. Category normalized name
    # =========================================================

    op.add_column(
        "categories",
        sa.Column(
            "name_normalized",
            sa.Unicode(length=100),
            nullable=True,
        ),
    )

    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.Unicode(100)),
        sa.column(
            "name_normalized",
            sa.Unicode(100),
        ),
    )

    category_rows = bind.execute(
        sa.select(
            categories.c.id,
            categories.c.name,
        )
        .order_by(categories.c.id)
    ).fetchall()

    normalized_categories = (
        _validate_no_duplicates(
            category_rows,
            _normalize_category_name,
            "los nombres de categoría",
        )
    )

    for row in category_rows:
        display_name = (
            _normalize_category_display_name(
                row.name
            )
        )

        normalized_name = (
            _normalize_category_name(
                display_name
            )
        )

        if len(display_name) > 100:
            raise RuntimeError(
                "El nombre normalizado de categoría "
                f"id={row.id} supera los 100 caracteres."
            )

        bind.execute(
            categories.update()
            .where(
                categories.c.id == row.id
            )
            .values(
                name=display_name,
                name_normalized=normalized_name,
            )
        )

    # La unicidad antigua de name depende de la
    # semántica/collation del motor.
    op.drop_constraint(
        "uq_categories_name",
        "categories",
        type_="unique",
    )

    op.alter_column(
        "categories",
        "name_normalized",
        existing_type=sa.Unicode(length=100),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_categories_name_normalized",
        "categories",
        ["name_normalized"],
    )


def downgrade():
    bind = op.get_bind()

    categories = sa.table(
        "categories",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.Unicode(100)),
        sa.column(
            "name_normalized",
            sa.Unicode(100),
        ),
    )

    # Restaurar constraint anterior.
    op.drop_constraint(
        "uq_categories_name_normalized",
        "categories",
        type_="unique",
    )

    op.create_unique_constraint(
        "uq_categories_name",
        "categories",
        ["name"],
    )

    op.drop_column(
        "categories",
        "name_normalized",
    )