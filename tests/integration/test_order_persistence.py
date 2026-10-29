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
from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)

def _unique_suffix():
    return uuid4().hex[:10]


class FixedDeliveryPricingService:
    def normalize_coordinates(
        self,
        latitude,
        longitude,
    ):
        return DeliveryPricingService.normalize_coordinates(
            latitude,
            longitude,
        )

    def quote(
        self,
        latitude,
        longitude,
    ):
        return {
            "latitude": latitude,
            "longitude": longitude,
            "straight_distance_km": Decimal("1.20"),
            "distance_km": Decimal("1.56"),
            "billable_km": 2,
            "delivery_fee": Decimal("5100.00"),
            "base_fee": Decimal("3500.00"),
            "price_per_km": Decimal("800.00"),
            "distance_factor": Decimal("1.30"),
        }


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

        request_key = str(uuid4())

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
            idempotency_key=request_key,
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

        replayed_order = service.create_order(
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
            idempotency_key=request_key,
        )

        assert replayed_order.id == order.id
        assert replayed_order.idempotency_replayed is True

        order_count = (
            integration_session.query(Order)
            .filter_by(
                idempotency_key=request_key,
            )
            .count()
        )

        assert order_count == 1


        integration_session.expire_all()

        persisted_order = (
            integration_session.get(
                Order,
                order.id,
            )
        )

        assert persisted_order is not None
        
        assert persisted_order.tracking_token == (
            order.tracking_token
        )

        assert len(
            persisted_order.tracking_token
        ) == 43

        tracked_order = service.get_order_tracking(
            persisted_order.tracking_token
        )

        assert tracked_order is not None
        assert tracked_order.id == persisted_order.id
        assert tracked_order.status == persisted_order.status
        assert tracked_order.total == persisted_order.total

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

        # Verificar la persistencia de todas las transiciones
        # del ciclo de preparación y entrega.
        expected_transitions = (
            "confirmed",
            "preparing",
            "shipped",
            "delivered",
        )

        for expected_status in expected_transitions:
            updated_order = service.update_admin_order_status(
                order.id,
                expected_status,
            )

            assert updated_order is not None
            assert updated_order.status == expected_status

        integration_session.expire_all()

        persisted_history = (
            integration_session.query(
                OrderStatusHistory
            )
            .filter(
                OrderStatusHistory.order_id == order.id
            )
            .order_by(
                OrderStatusHistory.changed_at,
                OrderStatusHistory.id,
            )
            .all()
        )

        assert [
            entry.new_status
            for entry in persisted_history
        ] == [
            "pending",
            "confirmed",
            "preparing",
            "shipped",
            "delivered",
        ]

        # La regeneración debe persistir en la base de datos
        # y dejar de reconocer el token anterior.
        current_order = service.get_order(order.id)

        old_tracking_token = current_order.tracking_token

        rotated_order = (
            service.rotate_admin_order_tracking_token(
                order.id
            )
        )

        assert rotated_order is not None
        assert rotated_order.tracking_token != old_tracking_token

        integration_session.expire_all()

        rotated_persisted_order = integration_session.get(
            Order,
            order.id,
        )

        assert rotated_persisted_order.tracking_token == (
            rotated_order.tracking_token
        )

        assert (
            service.get_order_tracking(old_tracking_token)
            is None
        )

        assert service.get_order_tracking(
            rotated_order.tracking_token
        ).id == order.id

        assert [
            entry.previous_status
            for entry in persisted_history
        ] == [
            None,
            "pending",
            "confirmed",
            "preparing",
            "shipped",
        ]

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


@pytest.mark.integration
def test_order_delivery_quote_is_persisted_and_reloaded(
    integration_session,
):
    category = None
    product = None
    order = None

    try:
        category_repository = SQLAlchemyCategoryRepository(
            session=integration_session
        )

        product_repository = SQLAlchemyProductRepository(
            session=integration_session
        )

        order_repository = SQLAlchemyOrderRepository(
            session=integration_session
        )

        suffix = _unique_suffix()

        category = category_repository.create(
            CategoryEntity(
                id=None,
                name=f"Delivery Test {suffix}",
                slug=f"delivery-test-{suffix}",
                is_active=True,
            )
        )

        product = product_repository.create(
            ProductEntity(
                id=None,
                code=f"DELIVERY-{suffix.upper()}",
                name="Producto para prueba de domicilio",
                description=None,
                price=Decimal("25000.50"),
                category_id=category.id,
                image_url=None,
                is_active=True,
            )
        )

        service = OrderService(
            repository=order_repository,
            product_repository=product_repository,
            delivery_pricing_service=(
                FixedDeliveryPricingService()
            ),
        )

        order = service.create_order(
            name="Cliente de prueba domicilio",
            phone="3001234567",
            city="Medellín",
            address="Calle 10 # 25-30",
            observations=None,
            items=[
                {
                    "product_id": product.id,
                    "quantity": 2,
                }
            ],
            idempotency_key=str(uuid4()),
            delivery_latitude="6.2542000",
            delivery_longitude="-75.5812000",
        )

        expected_subtotal = Decimal("50001.00")
        expected_delivery_fee = Decimal("5100.00")
        expected_total = Decimal("55101.00")

        assert order.delivery_fee == expected_delivery_fee
        assert order.total == expected_total

        assert order.delivery_latitude == Decimal(
            "6.2542000"
        )

        assert order.delivery_longitude == Decimal(
            "-75.5812000"
        )

        assert order.delivery_straight_distance_km == (
            Decimal("1.20")
        )

        assert order.delivery_distance_km == (
            Decimal("1.56")
        )

        assert order.delivery_billable_km == 2

        integration_session.expire_all()

        persisted_model = integration_session.get(
            Order,
            order.id,
        )

        assert persisted_model is not None
        assert persisted_model.delivery_fee == (
            expected_delivery_fee
        )
        assert persisted_model.total == expected_total
        assert persisted_model.delivery_billable_km == 2

        loaded_order = order_repository.get_by_id(
            order.id
        )

        assert loaded_order is not None
        assert loaded_order.delivery_fee == (
            expected_delivery_fee
        )
        assert loaded_order.total == expected_total
        assert loaded_order.delivery_distance_km == (
            Decimal("1.56")
        )

        loaded_subtotal = sum(
            (
                item.line_total
                for item in loaded_order.items
            ),
            Decimal("0.00"),
        )

        assert loaded_subtotal == expected_subtotal
        assert (
            loaded_subtotal + loaded_order.delivery_fee
            == loaded_order.total
        )

    finally:
        if order is not None:
            persisted_order = integration_session.get(
                Order,
                order.id,
            )

            if persisted_order is not None:
                integration_session.delete(
                    persisted_order
                )
                integration_session.commit()

        if product is not None:
            persisted_product = integration_session.get(
                Product,
                product.id,
            )

            if persisted_product is not None:
                integration_session.delete(
                    persisted_product
                )
                integration_session.commit()

        if category is not None:
            persisted_category = integration_session.get(
                Category,
                category.id,
            )

            if persisted_category is not None:
                integration_session.delete(
                    persisted_category
                )
                integration_session.commit()