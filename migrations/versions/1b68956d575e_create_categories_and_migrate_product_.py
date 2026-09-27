"""create categories and migrate product categories

Revision ID: 1b68956d575e
Revises: b858facc4a3a
Create Date: 2026-09-09 21:55:44.843067

"""
from collections import OrderedDict
import re
import unicodedata

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1b68956d575e"
down_revision = "b858facc4a3a"
branch_labels = None
depends_on = None


def _normalize_category_name(value):
    """Normaliza un nombre de categoría para comparaciones."""
    if value is None:
        return None

    value = " ".join(str(value).strip().split())

    if not value:
        return None

    return value.casefold()


def _display_category_name(value):
    """Obtiene el nombre visible de la categoría."""
    value = " ".join(str(value).strip().split())

    if not value:
        return None

    return value


def _slugify(value):
    """Genera un slug independiente de dependencias externas."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()

    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    normalized = normalized.strip("-")

    return normalized


def _build_unique_slug(base_slug, used_slugs):
    """Genera un slug único."""
    if base_slug not in used_slugs:
        used_slugs.add(base_slug)
        return base_slug

    counter = 2

    while f"{base_slug}-{counter}" in used_slugs:
        counter += 1

    slug = f"{base_slug}-{counter}"
    used_slugs.add(slug)

    return slug


def upgrade():
    bind = op.get_bind()

    # ---------------------------------------------------------
    # 1. Crear tabla categories
    # ---------------------------------------------------------
    op.create_table(
        "categories",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "slug",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name",
            name="uq_categories_name",
        ),
        sa.UniqueConstraint(
            "slug",
            name="uq_categories_slug",
        ),
    )

    # ---------------------------------------------------------
    # 2. Agregar category_id a products temporalmente nullable
    # ---------------------------------------------------------
    op.add_column(
        "products",
        sa.Column(
            "category_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # ---------------------------------------------------------
    # 3. Leer categorías existentes de products.category
    # ---------------------------------------------------------
    products_table = sa.table(
        "products",
        sa.column("id", sa.Integer()),
        sa.column("category", sa.String(length=100)),
        sa.column("category_id", sa.Integer()),
    )

    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(length=100)),
        sa.column("slug", sa.String(length=100)),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    product_rows = bind.execute(
        sa.select(
            products_table.c.id,
            products_table.c.category,
        ).order_by(products_table.c.id)
    ).fetchall()

    # ---------------------------------------------------------
    # 4. Validar categorías existentes
    # ---------------------------------------------------------
    normalized_categories = OrderedDict()

    for row in product_rows:
        original_category = row.category
        normalized_name = _normalize_category_name(original_category)

        if normalized_name is None:
            raise RuntimeError(
                "No se puede migrar la columna products.category porque "
                f"el producto con id={row.id} tiene una categoría vacía o nula."
            )

        if normalized_name not in normalized_categories:
            display_name = _display_category_name(original_category)

            if len(display_name) > 100:
                raise RuntimeError(
                    "No se puede migrar la categoría del producto "
                    f"con id={row.id}: el nombre supera los 100 caracteres."
                )

            normalized_categories[normalized_name] = display_name

    # ---------------------------------------------------------
    # 5. Crear una categoría por cada valor existente
    #
    # Se consolidan diferencias de:
    # - mayúsculas/minúsculas
    # - espacios iniciales/finales
    # - espacios repetidos
    #
    # Ejemplo:
    # "Amigurumis"
    # " amigurumis "
    # "AMIGURUMIS"
    #
    # => una sola categoría: "Amigurumis"
    # ---------------------------------------------------------
    used_slugs = set()
    category_ids = {}

    for normalized_name, display_name in normalized_categories.items():
        base_slug = _slugify(display_name)

        if not base_slug:
            raise RuntimeError(
                "No se pudo generar un slug válido para la categoría "
                f"'{display_name}'."
            )

        slug = _build_unique_slug(base_slug, used_slugs)

        bind.execute(
            sa.insert(categories_table).values(
                name=display_name,
                slug=slug,
                is_active=True,
            )
        )

        category_id = bind.execute(
            sa.select(categories_table.c.id).where(
                categories_table.c.slug == slug
            )
        ).scalar_one()

        category_ids[normalized_name] = category_id

    # ---------------------------------------------------------
    # 6. Asignar category_id a cada producto
    # ---------------------------------------------------------
    for row in product_rows:
        normalized_name = _normalize_category_name(row.category)
        category_id = category_ids[normalized_name]

        bind.execute(
            products_table.update()
            .where(products_table.c.id == row.id)
            .values(category_id=category_id)
        )

    # ---------------------------------------------------------
    # 7. Verificar que todos los productos tengan category_id
    # ---------------------------------------------------------
    products_without_category = bind.execute(
        sa.select(sa.func.count())
        .select_from(products_table)
        .where(products_table.c.category_id.is_(None))
    ).scalar_one()

    if products_without_category:
        raise RuntimeError(
            "La migración no pudo asignar category_id a todos los productos."
        )

    # ---------------------------------------------------------
    # 8. Crear FK products.category_id -> categories.id
    # ---------------------------------------------------------
    op.create_foreign_key(
        "fk_products_category_id_categories",
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )

    # ---------------------------------------------------------
    # 9. Hacer category_id obligatorio
    # ---------------------------------------------------------
    op.alter_column(
        "products",
        "category_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # ---------------------------------------------------------
    # 10. Eliminar la antigua columna category
    # ---------------------------------------------------------
    op.drop_column(
        "products",
        "category",
    )


def downgrade():
    bind = op.get_bind()

    products_table = sa.table(
        "products",
        sa.column("id", sa.Integer()),
        sa.column("category_id", sa.Integer()),
    )

    categories_table = sa.table(
        "categories",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String(length=100)),
    )

    # 1. Restaurar la columna category.
    op.add_column(
        "products",
        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # 2. Recuperar el nombre de la categoría.
    rows = bind.execute(
        sa.select(
            products_table.c.id,
            products_table.c.category_id,
            categories_table.c.name,
        ).select_from(
            products_table.join(
                categories_table,
                products_table.c.category_id
                == categories_table.c.id,
            )
        )
    ).fetchall()

    for row in rows:
        bind.execute(
            products_table.update()
            .where(products_table.c.id == row.id)
            .values(category=row.name)
        )

    # 3. El downgrade no debe continuar si algún producto
    #    quedó sin categoría.
    products_with_null_category = bind.execute(
        sa.select(sa.func.count())
        .select_from(
            sa.table(
                "products",
                sa.column(
                    "category",
                    sa.String(length=100),
                ),
            )
        )
        .where(
            sa.table(
                "products",
                sa.column(
                    "category",
                    sa.String(length=100),
                ),
            ).c.category.is_(None)
        )
    ).scalar_one()

    if products_with_null_category:
        raise RuntimeError(
            "No se puede revertir la migración porque existen "
            "productos sin categoría."
        )

    # 4. category vuelve a ser obligatorio.
    op.alter_column(
        "products",
        "category",
        existing_type=sa.String(length=100),
        nullable=False,
    )

    # 5. Eliminar FK.
    op.drop_constraint(
        "fk_products_category_id_categories",
        "products",
        type_="foreignkey",
    )

    # 6. Eliminar category_id.
    op.drop_column(
        "products",
        "category_id",
    )

    # 7. Eliminar categories.
    op.drop_table(
        "categories",
    )