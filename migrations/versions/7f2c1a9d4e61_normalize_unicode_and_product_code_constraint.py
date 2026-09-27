"""normalize unicode columns and product code constraint

Revision ID: 7f2c1a9d4e61
Revises: 1b68956d575e
Create Date: 2026-09-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7f2c1a9d4e61"
down_revision = "1b68956d575e"
branch_labels = None
depends_on = None


def upgrade():
    # =========================================================
    # 1. Remove objects that depend on columns being altered
    # =========================================================

    # admin_users.email
    #
    # The current schema contains:
    #     ix_admin_users_email
    #
    # It must be removed before changing VARCHAR -> NVARCHAR
    # on SQL Server.
    op.drop_index(
        "ix_admin_users_email",
        table_name="admin_users",
    )

    # categories.name / categories.slug
    #
    # These columns participate in unique constraints, so the
    # constraints must be removed before changing their type.
    op.drop_constraint(
        "uq_categories_name",
        "categories",
        type_="unique",
    )

    op.drop_constraint(
        "uq_categories_slug",
        "categories",
        type_="unique",
    )

    # products.code
    #
    # Historical migration created this as a unique index.
    op.drop_index(
        "ix_products_code",
        table_name="products",
    )

    # =========================================================
    # 2. Alter columns to Unicode-capable types
    # =========================================================

    # -------------------------
    # admin_users
    # -------------------------

    op.alter_column(
        "admin_users",
        "email",
        existing_type=sa.String(length=255),
        type_=sa.Unicode(length=255),
        existing_nullable=False,
    )

    op.alter_column(
        "admin_users",
        "password_hash",
        existing_type=sa.String(length=255),
        type_=sa.Unicode(length=255),
        existing_nullable=False,
    )

    # -------------------------
    # categories
    # -------------------------

    op.alter_column(
        "categories",
        "name",
        existing_type=sa.String(length=100),
        type_=sa.Unicode(length=100),
        existing_nullable=False,
    )

    op.alter_column(
        "categories",
        "slug",
        existing_type=sa.String(length=100),
        type_=sa.Unicode(length=100),
        existing_nullable=False,
    )

    # -------------------------
    # products
    # -------------------------

    op.alter_column(
        "products",
        "code",
        existing_type=sa.String(length=50),
        type_=sa.Unicode(length=50),
        existing_nullable=False,
    )

    op.alter_column(
        "products",
        "name",
        existing_type=sa.String(length=150),
        type_=sa.Unicode(length=150),
        existing_nullable=False,
    )

    op.alter_column(
        "products",
        "description",
        existing_type=sa.Text(),
        type_=sa.UnicodeText(),
        existing_nullable=True,
    )

    op.alter_column(
        "products",
        "image_url",
        existing_type=sa.String(length=500),
        type_=sa.Unicode(length=500),
        existing_nullable=True,
    )

    # =========================================================
    # 3. Recreate dependent objects
    # =========================================================

    # admin_users.email
    #
    # Restore the original unique index expected by the model.
    op.create_index(
        "ix_admin_users_email",
        "admin_users",
        ["email"],
        unique=True,
    )

    # categories.name
    op.create_unique_constraint(
        "uq_categories_name",
        "categories",
        ["name"],
    )

    # categories.slug
    op.create_unique_constraint(
        "uq_categories_slug",
        "categories",
        ["slug"],
    )

    # products.code
    #
    # Normalize the historical unique index into the named
    # unique constraint represented by the current model.
    op.create_unique_constraint(
        "uq_products_code",
        "products",
        ["code"],
    )


def downgrade():
    # =========================================================
    # 1. Remove dependent objects
    # =========================================================

    op.drop_index(
        "ix_admin_users_email",
        table_name="admin_users",
    )

    op.drop_constraint(
        "uq_categories_name",
        "categories",
        type_="unique",
    )

    op.drop_constraint(
        "uq_categories_slug",
        "categories",
        type_="unique",
    )

    op.drop_constraint(
        "uq_products_code",
        "products",
        type_="unique",
    )

    # =========================================================
    # 2. Restore original column types
    # =========================================================

    # -------------------------
    # admin_users
    # -------------------------

    op.alter_column(
        "admin_users",
        "password_hash",
        existing_type=sa.Unicode(length=255),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    op.alter_column(
        "admin_users",
        "email",
        existing_type=sa.Unicode(length=255),
        type_=sa.String(length=255),
        existing_nullable=False,
    )

    # -------------------------
    # categories
    # -------------------------

    op.alter_column(
        "categories",
        "slug",
        existing_type=sa.Unicode(length=100),
        type_=sa.String(length=100),
        existing_nullable=False,
    )

    op.alter_column(
        "categories",
        "name",
        existing_type=sa.Unicode(length=100),
        type_=sa.String(length=100),
        existing_nullable=False,
    )

    # -------------------------
    # products
    # -------------------------

    op.alter_column(
        "products",
        "image_url",
        existing_type=sa.Unicode(length=500),
        type_=sa.String(length=500),
        existing_nullable=True,
    )

    op.alter_column(
        "products",
        "description",
        existing_type=sa.UnicodeText(),
        type_=sa.Text(),
        existing_nullable=True,
    )

    op.alter_column(
        "products",
        "name",
        existing_type=sa.Unicode(length=150),
        type_=sa.String(length=150),
        existing_nullable=False,
    )

    op.alter_column(
        "products",
        "code",
        existing_type=sa.Unicode(length=50),
        type_=sa.String(length=50),
        existing_nullable=False,
    )

    # =========================================================
    # 3. Restore original dependent objects
    # =========================================================

    op.create_index(
        "ix_admin_users_email",
        "admin_users",
        ["email"],
        unique=True,
    )

    op.create_unique_constraint(
        "uq_categories_name",
        "categories",
        ["name"],
    )

    op.create_unique_constraint(
        "uq_categories_slug",
        "categories",
        ["slug"],
    )

    op.create_index(
        "ix_products_code",
        "products",
        ["code"],
        unique=True,
    )