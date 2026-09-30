from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.services.order_service import (
    OrderService,
)


class FakeProductRepository:
    def __init__(
        self,
        products=None,
    ):
        self.products = {
            product.id: product
            for product in (
                products or []
            )
        }
        self.active_calls = []

    def get_active_by_id(
        self,
        product_id,
    ):
        self.active_calls.append(
            product_id
        )

        product = self.products.get(
            product_id
        )

        if (
            product is None
            or not product.is_active
        ):
            return None

        return product


class FakeOrderRepository:
    def __init__(self):
        self.created_orders = []
        self.next_id = 1

    def create(
        self,
        order,
    ):
        order.id = self.next_id

        self.next_id += 1

        self.created_orders.append(
            order
        )

        return order

    def get_by_id(
        self,
        order_id,
    ):
        for order in self.created_orders:
            if order.id == order_id:
                return order

        return None


def _product(
    product_id=1,
    price="85000.00",
    is_active=True,
):
    return SimpleNamespace(
        id=product_id,
        code=(
            f"LL-{product_id:03d}"
        ),
        name=(
            f"Producto {product_id}"
        ),
        price=Decimal(price),
        is_active=is_active,
    )


def _service(
    products=None,
):
    return OrderService(
        repository=FakeOrderRepository(),
        product_repository=FakeProductRepository(
            products=products
            or [
                _product()
            ]
        ),
    )


def test_create_order_calculates_server_side_total_and_snapshots_product():
    service = _service(
        products=[
            _product(
                product_id=1,
                price="85000.00",
            ),
            _product(
                product_id=2,
                price="12000.50",
            ),
        ]
    )

    order = service.create_order(
        name="  María   López ",
        phone="+57 300 123 4567",
        city="  Medellín  ",
        address="Calle 10 # 25-30",
        observations=(
            "  Entregar en la mañana. "
        ),
        items=[
            {
                "product_id": 1,
                "quantity": 2,
            },
            {
                "product_id": 2,
                "quantity": 3,
            },
        ],
    )

    assert order.id == 1
    assert order.customer_name == (
        "María López"
    )
    assert order.phone == (
        "+57 300 123 4567"
    )
    assert order.city == "Medellín"
    assert order.observations == (
        "Entregar en la mañana."
    )
    assert order.address == (
        "Calle 10 # 25-30"
    )
    assert order.status == "pending"
    assert order.total == (
        Decimal("206001.50")
    )

    assert len(order.items) == 2

    assert order.items[0].product_id == 1
    assert order.items[0].product_code == (
        "LL-001"
    )
    assert order.items[0].product_name == (
        "Producto 1"
    )
    assert order.items[0].unit_price == (
        Decimal("85000.00")
    )
    assert order.items[0].quantity == 2
    assert order.items[0].line_total == (
        Decimal("170000.00")
    )

    assert order.items[1].product_id == 2
    assert order.items[1].line_total == (
        Decimal("36001.50")
    )


@pytest.mark.parametrize(
    "payload, message",
    [
        (
            {
                "name": "",
                "phone": "3001234567",
                "city": "Medellín",
                "address": "Calle 10 # 25-30",
                "observations": None,
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 1,
                    }
                ],
            },
            "El nombre es obligatorio",
        ),
        (
            {
                "name": "María",
                "phone": "",
                "city": "Medellín",
                "address": "Calle 10 # 25-30",
                "observations": None,
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 1,
                    }
                ],
            },
            "El teléfono es obligatorio",
        ),
        (
            {
                "name": "María",
                "phone": "3001234567",
                "city": "",
                "address": "Calle 10 # 25-30",
                "observations": None,
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 1,
                    }
                ],
            },
            "La ciudad es obligatoria",
        ),
        (
            {
                "name": "María",
                "phone": "abc3001234",
                "city": "Medellín",
                "address": "Calle 10 # 25-30",
                "observations": None,
                "items": [
                    {
                        "product_id": 1,
                        "quantity": 1,
                    }
                ],
            },
            "caracteres no válidos",
        ),
        (
            {
                "name": "María",
                "phone": "3001234567",
                "city": "Medellín",
                "address": "Calle 10 # 25-30",
                "observations": None,
                "items": [],
            },
            "al menos un producto",
        ),
    ],
)
def test_create_order_rejects_invalid_customer_or_items(
    payload,
    message,
):
    service = _service()

    with pytest.raises(
        ValueError,
        match=message,
    ):
        service.create_order(
            **payload
        )


def test_create_order_rejects_duplicate_products():
    service = _service()

    with pytest.raises(
        ValueError,
        match="no puede repetir",
    ):
        service.create_order(
            name="María",
            phone="3001234567",
            city="Medellín",
            address="Calle 10 # 25-30",
            observations=None,
            items=[
                {
                    "product_id": 1,
                    "quantity": 1,
                },
                {
                    "product_id": 1,
                    "quantity": 2,
                },
            ],
        )


def test_create_order_rejects_unavailable_product():
    service = _service(
        products=[
            _product(
                product_id=1,
                is_active=False,
            )
        ]
    )

    with pytest.raises(
        ValueError,
        match="ya no está disponible",
    ):
        service.create_order(
            name="María",
            phone="3001234567",
            city="Medellín",
            address="Calle 10 # 25-30",
            observations=None,
            items=[
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        )


def test_create_order_normalizes_blank_observations_to_none():
    service = _service()

    order = service.create_order(
        name="María",
        phone="3001234567",
        city="Medellín",
        address="Calle 10 # 25-30",
        observations="   ",
        items=[
            {
                "product_id": 1,
                "quantity": 1,
            }
        ],
    )

    assert order.observations is None


def test_create_order_rejects_quantity_over_limit():
    service = _service()

    with pytest.raises(
        ValueError,
        match="no puede superar",
    ):
        service.create_order(
            name="María",
            phone="3001234567",
            city="Medellín",
            address="Calle 10 # 25-30",
            observations=None,
            items=[
                {
                    "product_id": 1,
                    "quantity": 100,
                }
            ],
        )


def test_get_order_validates_id():
    service = _service()

    with pytest.raises(
        ValueError,
        match="ID del pedido",
    ):
        service.get_order(0)


def test_create_order_rejects_empty_address():
    service = _service()

    with pytest.raises(
        ValueError,
        match="La dirección es obligatoria",
    ):
        service.create_order(
            name="María",
            phone="3001234567",
            city="Medellín",
            address="",
            observations=None,
            items=[
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        )


def test_create_order_rejects_address_over_limit():
    service = _service()

    with pytest.raises(
        ValueError,
        match="200 caracteres",
    ):
        service.create_order(
            name="María",
            phone="3001234567",
            city="Medellín",
            address="A" * 201,
            observations=None,
            items=[
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        )