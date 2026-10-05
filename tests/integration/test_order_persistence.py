from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.services.order_service import (
    OrderService,
)
from app.domain.entities.category import (
    CategoryEntity,
)
from app.domain.entities.product import (
    ProductEntity,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.order_model import (
    Order,
    OrderItem,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.order_repository_impl import (
    SQLAlchemyOrderRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)
from app.infrastructure.database.models.order_status_history_model import (
    OrderStatusHistory,
)


def _unique_suffix():
    return uuid4().hex[:10]


@pytest.mark.integration
def test_create_order_persists_header_items_and_total(
    integration_session,
):
    category = None
    product = None
    order = None

    try:
        category_repository = (
            SQLAlchemyCategoryRepository(
                session=integration_session
            )
        )

        category = category_repository.create(
            CategoryEntity(
                id=None,
                name=(
                    "Order Category "
                    f"{_unique_suffix()}"
                ),
                slug=(
                    "order-category-"
                    f"{_unique_suffix()}"
                ),
                is_active=True,
            )
        )

        product_repository = (
            SQLAlchemyProductRepository(
                session=integration_session
            )
        )

        product = product_repository.create(
            ProductEntity(
                id=None,
                code=(
                    "ORDER-"
                    f"{_unique_suffix().upper()}"
                ),
                name="Producto para pedido",
                description=None,
                price=Decimal("25000.50"),
                category_id=category.id,
                image_url=None,
                is_active=True,
            )
        )

        order_repository = (
            SQLAlchemyOrderRepository(
                session=integration_session
            )
        )

        service = OrderService(
            repository=order_repository,
            product_repository=product_repository,
        )

        order = service.create_order(
            name="Cliente Integración",
            phone="3001234567",
            city="Medellín",
            address="Calle 10 # 25-30",
            observations="Pedido de prueba.",
            items=[
                {
                    "product_id": product.id,
                    "quantity": 3,
                }
            ],
        )

        assert order.id is not None
        assert order.address == (
            "Calle 10 # 25-30"
        )
        assert order.total == (
            Decimal("75001.50")
        )
        assert len(order.items) == 1
        assert len(
            order.status_history
        ) == 1

        assert (
            order.status_history[0].order_id
            == order.id
        )

        assert (
            order.status_history[0].previous_status
            is None
        )

        assert (
            order.status_history[0].new_status
            == "pending"
        )

        assert (
            order.status_history[0].changed_at
            is not None
        )
        assert order.items[0].product_id == (
            product.id
        )
        assert order.items[0].unit_price == (
            Decimal("25000.50")
        )
        assert order.items[0].line_total == (
            Decimal("75001.50")
        )

        integration_session.expire_all()

        persisted_order = (
            integration_session.get(
                Order,
                order.id,
            )
        )

        assert persisted_order is not None
        assert persisted_order.customer_name == (
            "Cliente Integración"
        )
        assert persisted_order.status == (
            "pending"
        )
        assert persisted_order.total == (
            Decimal("75001.50")
        )
        assert persisted_order.address == (
            "Calle 10 # 25-30"
        )

        persisted_items = (
            integration_session.query(
                OrderItem
            )
            .filter(
                OrderItem.order_id == order.id
            )
            .all()
        )

        persisted_history = (
            integration_session.query(
                OrderStatusHistory
            )
            .filter(
                OrderStatusHistory.order_id
                == order.id
            )
            .all()
        )

        assert len(
            persisted_history
        ) == 1

        assert (
            persisted_history[0].previous_status
            is None
        )

        assert (
            persisted_history[0].new_status
            == "pending"
        )

        assert len(persisted_items) == 1
        assert persisted_items[0].product_code == (
            product.code
        )
        assert persisted_items[0].product_name == (
            product.name
        )
        assert persisted_items[0].quantity == 3
        assert persisted_items[0].line_total == (
            Decimal("75001.50")
        )

    finally:
        persisted_order = (
            integration_session.get(
                Order,
                order.id,
            )
            if order is not None
            else None
        )

        if persisted_order is not None:
            integration_session.delete(
                persisted_order
            )
            integration_session.commit()

        persisted_product = (
            integration_session.get(
                Product,
                product.id,
            )
            if product is not None
            else None
        )

        if persisted_product is not None:
            integration_session.delete(
                persisted_product
            )
            integration_session.commit()

        persisted_category = (
            integration_session.get(
                Category,
                category.id,
            )
            if category is not None
            else None
        )

        if persisted_category is not None:
            integration_session.delete(
                persisted_category
            )
            integration_session.commit()