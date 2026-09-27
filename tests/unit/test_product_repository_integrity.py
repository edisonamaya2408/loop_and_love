from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product


def test_duplicate_product_code_database_error(
    app,
):
    code = (
        f"INTEGRITY-{uuid4().hex[:12].upper()}"
    )

    with app.app_context():
        category_suffix = uuid4().hex[:8]

        category = Category(
            name=f"Test {category_suffix}",
            slug=f"test-{category_suffix}",
            is_active=True,
        )

        db.session.add(category)
        db.session.flush()

        first_product = Product(
            code=code,
            name="Producto existente",
            description=None,
            price=Decimal("10000"),
            category_id=category.id,
            image_url=None,
            is_active=True,
        )

        db.session.add(first_product)
        db.session.commit()

        try:
            duplicate_product = Product(
                code=code,
                name="Producto duplicado",
                description=None,
                price=Decimal("20000"),
                category_id=category.id,
                image_url=None,
                is_active=True,
            )

            db.session.add(
                duplicate_product
            )

            with pytest.raises(
                IntegrityError
            ) as exc_info:
                db.session.commit()

            db.session.rollback()

            assert exc_info.value.orig is not None

            message = str(
                exc_info.value.orig
            ).lower()

            assert (
                "duplicate key" in message
                or "unique" in message
            )

        finally:
            db.session.rollback()

            persisted_product = (
                Product.query.filter_by(
                    code=code
                ).first()
            )

            if persisted_product is not None:
                db.session.delete(
                    persisted_product
                )
                db.session.commit()

            persisted_category = (
                Category.query.filter_by(
                    id=category.id
                ).first()
            )

            if persisted_category is not None:
                db.session.delete(
                    persisted_category
                )
            db.session.commit()