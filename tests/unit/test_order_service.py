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
    def __init__(
        self,
        paginated_orders=None,
        paginated_total=None,
    ):
        self.created_orders = []
        self.next_id = 1

        self.paginated_orders = (
            paginated_orders
            or []
        )

        self.paginated_total = (
            (
                len(
                    self.paginated_orders
                )
                if paginated_total is None
                else paginated_total
            )
        )

        self.paginated_calls = []

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

    def get_all_paginated(
        self,
        search=None,
        status=None,
        offset=0,
        limit=12,
    ):
        self.paginated_calls.append(
            {
                "search": search,
                "status": status,
                "offset": offset,
                "limit": limit,
            }
        )

        return (
            self.paginated_orders[
                offset:offset + limit
            ],
            self.paginated_total,
        )


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


def _admin_service(
    paginated_orders=None,
    paginated_total=None,
):
    repository = FakeOrderRepository(
        paginated_orders=paginated_orders,
        paginated_total=paginated_total,
    )

    service = OrderService(
        repository=repository,
        product_repository=FakeProductRepository(
            products=[
                _product()
            ]
        ),
    )

    return (
        service,
        repository,
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


def test_list_admin_orders_uses_default_pagination_and_returns_metadata():
    orders = [
        SimpleNamespace(
            id=15,
        ),
        SimpleNamespace(
            id=14,
        ),
    ]

    service, repository = _admin_service(
        paginated_orders=orders,
        paginated_total=27,
    )

    result = service.list_admin_orders()

    assert result.items == orders

    assert result.pagination.page == 1

    assert result.pagination.per_page == 12

    assert result.pagination.total == 27

    assert result.pagination.pages == 3

    assert result.pagination.has_next is True

    assert result.pagination.has_previous is False

    assert repository.paginated_calls == [
        {
            "search": None,
            "status": None,
            "offset": 0,
            "limit": 12,
        }
    ]


def test_list_admin_orders_normalizes_search_and_status():
    orders = [
        SimpleNamespace(
            id=15,
        ),
    ]

    service, repository = _admin_service(
        paginated_orders=orders,
        paginated_total=1,
    )

    result = service.list_admin_orders(
        search="  María López  ",
        status="  PENDING  ",
    )

    assert result.items == orders

    assert repository.paginated_calls == [
        {
            "search": "María López",
            "status": "pending",
            "offset": 0,
            "limit": 12,
        }
    ]


def test_list_admin_orders_converts_pagination_values():
    orders = [
        SimpleNamespace(
            id=10,
        ),
        SimpleNamespace(
            id=11,
        ),
        SimpleNamespace(
            id=12,
        ),
        SimpleNamespace(
            id=13,
        ),
        SimpleNamespace(
            id=14,
        ),
        SimpleNamespace(
            id=15,
        ),
    ]

    service, repository = _admin_service(
        paginated_orders=orders,
        paginated_total=20,
    )

    result = service.list_admin_orders(
        search="cliente",
        status="confirmed",
        page="2",
        per_page="5",
    )

    assert result.items == [
        SimpleNamespace(
            id=15,
        ),
    ]

    assert result.pagination.page == 2

    assert result.pagination.per_page == 5

    assert result.pagination.total == 20

    assert result.pagination.pages == 4

    assert result.pagination.has_next is True

    assert result.pagination.has_previous is True

    assert repository.paginated_calls == [
        {
            "search": "cliente",
            "status": "confirmed",
            "offset": 5,
            "limit": 5,
        }
    ]


def test_list_admin_orders_normalizes_blank_search_to_none():
    service, repository = _admin_service(
        paginated_orders=[],
        paginated_total=0,
    )

    result = service.list_admin_orders(
        search="   ",
    )

    assert result.items == []

    assert result.pagination.total == 0

    assert result.pagination.pages == 0

    assert result.pagination.has_next is False

    assert result.pagination.has_previous is False

    assert repository.paginated_calls == [
        {
            "search": None,
            "status": None,
            "offset": 0,
            "limit": 12,
        }
    ]


def test_update_admin_order_status_confirms_pending_order():
    pending_order = SimpleNamespace(
        id=15,
        status="pending",
    )

    service, repository = _admin_service(
        paginated_orders=[],
        paginated_total=0,
    )

    repository.get_by_id = (
        lambda order_id:
        pending_order
        if order_id == 15
        else None
    )

    repository.update_status = (
        lambda order_id, status:
        SimpleNamespace(
            id=order_id,
            status=status,
        )
    )

    result = (
        service.update_admin_order_status(
            15,
            "confirmed",
        )
    )

    assert result.id == 15

    assert result.status == (
        "confirmed"
    )


def test_update_admin_order_status_rejects_already_confirmed_order():
    confirmed_order = SimpleNamespace(
        id=15,
        status="confirmed",
    )

    service, repository = _admin_service(
        paginated_orders=[],
        paginated_total=0,
    )

    repository.get_by_id = (
        lambda order_id:
        confirmed_order
        if order_id == 15
        else None
    )

    with pytest.raises(
        ValueError,
        match="Solo se pueden modificar pedidos pendientes",
    ):
        service.update_admin_order_status(
            15,
            "cancelled",
        )


def test_update_admin_order_status_returns_none_for_missing_order():
    service, repository = _admin_service(
        paginated_orders=[],
        paginated_total=0,
    )

    repository.get_by_id = (
        lambda order_id: None
    )

    result = (
        service.update_admin_order_status(
            999,
            "confirmed",
        )
    )

    assert result is None
    

@pytest.mark.parametrize(
    "status",
    [
        "processing",
        "completed",
        "cancelledx",
        "",
        "invalid",
    ],
)
def test_list_admin_orders_rejects_invalid_status(
    status,
):
    service, repository = _admin_service()

    with pytest.raises(
        ValueError,
        match="estado del pedido",
    ):
        service.list_admin_orders(
            status=status,
        )

    assert repository.paginated_calls == []


@pytest.mark.parametrize(
    "status",
    [
        "pending",
        "confirmed",
        "cancelled",
    ],
)
def test_list_admin_orders_accepts_valid_statuses(
    status,
):
    service, repository = _admin_service(
        paginated_orders=[],
        paginated_total=0,
    )

    result = service.list_admin_orders(
        status=status,
    )

    assert result.items == []

    assert repository.paginated_calls == [
        {
            "search": None,
            "status": status,
            "offset": 0,
            "limit": 12,
        }
    ]