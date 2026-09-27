from decimal import Decimal

import pytest
from sqlalchemy import event

from app.application.services.product_service import (
    ProductService,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)


@pytest.mark.integration
def test_product_response_loading_uses_one_category_query(
    app,
    integration_session,
):
    category_one = Category(
        name="Performance Category One",
        slug="performance-category-one",
        is_active=True,
    )

    category_two = Category(
        name="Performance Category Two",
        slug="performance-category-two",
        is_active=True,
    )

    integration_session.add_all(
        [
            category_one,
            category_two,
        ]
    )

    integration_session.commit()

    products = [
        Product(
            code=f"PERF-{index:03d}",
            name=f"Performance Product {index}",
            description="Performance test.",
            price=Decimal("10000"),
            category_id=(
                category_one.id
                if index % 2 == 0
                else category_two.id
            ),
            image_url=None,
            is_active=True,
        )
        for index in range(10)
    ]

    integration_session.add_all(
        products
    )

    integration_session.commit()

    statements = []

    def before_cursor_execute(
        conn,
        cursor,
        statement,
        parameters,
        context,
        executemany,
    ):
        normalized = statement.strip().lower()

        if normalized.startswith(
            "select"
        ):
            statements.append(
                normalized
            )

    connection = (
        integration_session.connection()
    )

    event.listen(
        connection,
        "before_cursor_execute",
        before_cursor_execute,
    )

    try:
        product_repository = (
            SQLAlchemyProductRepository(
                session=integration_session
            )
        )

        category_repository = (
            SQLAlchemyCategoryRepository(
                session=integration_session
            )
        )

        service = ProductService(
            repository=product_repository,
            category_repository=category_repository,
        )

        result = (
            service.list_active_products_paginated(
                page=1,
                per_page=10,
            )
        )

        responses = service.to_responses(
            result.items
        )

        assert len(responses) == 10

        assert {
            response.category_id
            for response in responses
        } == {
            category_one.id,
            category_two.id,
        }

        category_selects = [
            statement
            for statement in statements
            if "from categories" in statement
        ]

        assert len(
            category_selects
        ) == 1

    finally:
        event.remove(
            connection,
            "before_cursor_execute",
            before_cursor_execute,
        )

        for product in products:
            persisted = integration_session.get(
                Product,
                product.id,
            )

            if persisted is not None:
                integration_session.delete(
                    persisted
                )

        persisted_category_one = (
            integration_session.get(
                Category,
                category_one.id,
            )
        )

        if persisted_category_one is not None:
            integration_session.delete(
                persisted_category_one
            )

        persisted_category_two = (
            integration_session.get(
                Category,
                category_two.id,
            )
        )

        if persisted_category_two is not None:
            integration_session.delete(
                persisted_category_two
            )

        integration_session.commit()