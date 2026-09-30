from datetime import datetime, timezone
from decimal import Decimal

from app import create_app
from app.presentation.routes import order_routes


class FakeOrderService:
    def __init__(self):
        self.create_calls = []

    def create_order(
        self,
        name,
        phone,
        city,
        address,
        observations,
        items,
    ):
        self.create_calls.append(
            {
                "name": name,
                "phone": phone,
                "city": city,
                "address": address,
                "observations": observations,
                "items": items,
            }
        )

        return type(
            "Order",
            (),
            {
                "id": 15,
                "customer_name": name,
                "phone": phone,
                "city": city,
                "address": "Calle 10 # 25-30",
                "observations": observations,
                "status": "pending",
                "items": [
                    type(
                        "OrderItem",
                        (),
                        {
                            "product_id": 1,
                            "product_code": "LL-001",
                            "product_name": "Amigurumi Oso",
                            "unit_price": Decimal("85000.00"),
                            "quantity": 2,
                            "line_total": Decimal("170000.00"),
                        },
                    )()
                ],
                "total": Decimal("170000.00"),
                "created_at": datetime(
                    2026,
                    9,
                    29,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                "updated_at": datetime(
                    2026,
                    9,
                    29,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
            },
        )()


def _create_app(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app(
        "development"
    )

    service = FakeOrderService()

    monkeypatch.setattr(
        order_routes,
        "OrderService",
        lambda *args, **kwargs: service,
    )

    app.extensions[
        "_test_order_service"
    ] = service

    return app


def test_create_order_returns_created_order(
    monkeypatch,
):
    app = _create_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/orders",
        json={
            "name": "María López",
            "phone": "+57 300 123 4567",
            "city": "Medellín",
            "address": "Calle 10 # 25-30",
            "observations": (
                "Entregar mañana."
            ),
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == 15
    assert data["data"]["name"] == (
        "María López"
    )
    assert data["data"]["phone"] == (
        "+57 300 123 4567"
    )
    assert data["data"]["city"] == (
        "Medellín"
    )
    assert data["data"]["address"] == (
        "Calle 10 # 25-30"
    )
    assert data["data"]["status"] == (
        "pending"
    )

    assert data["data"]["items"][0] == {
        "product_id": 1,
        "code": "LL-001",
        "name": "Amigurumi Oso",
        "unit_price": "85000.00",
        "quantity": 2,
        "line_total": "170000.00",
    }

    assert data["data"]["total"] == (
        "170000.00"
    )

    service = app.extensions[
        "_test_order_service"
    ]

    assert service.create_calls == [
        {
            "name": "María López",
            "phone": "+57 300 123 4567",
            "city": "Medellín",
            "address": "Calle 10 # 25-30",
            "observations": (
                "Entregar mañana."
            ),
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                }
            ],
        }
    ]


def test_create_order_requires_json(
    monkeypatch,
):
    app = _create_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/orders",
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "INVALID_REQUEST"
    )


def test_create_order_is_public(
    monkeypatch,
):
    app = _create_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/orders",
        json={
            "name": "María López",
            "phone": "3001234567",
            "city": "Medellín",
            "observations": None,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 201