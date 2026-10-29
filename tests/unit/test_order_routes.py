from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app import create_app
from app.presentation.routes import order_routes
from types import SimpleNamespace


class FakeOrderService:
    def __init__(self):
        self.create_calls = []
        self.tracking_order = None
        self.tracking_calls = []

    def create_order(
        self,
        name,
        phone,
        city,
        address,
        observations,
        items,
        idempotency_key=None,
        delivery_latitude=None,
        delivery_longitude=None,
    ):
        self.create_calls.append(
            {
                "name": name,
                "phone": phone,
                "city": city,
                "address": address,
                "observations": observations,
                "items": items,
                "idempotency_key": idempotency_key,
                "delivery_latitude": delivery_latitude,
                "delivery_longitude": delivery_longitude,
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
                "tracking_token": "a" * 43,
            },
        )()


    def get_order_tracking(
        self,
        tracking_token,
    ):
        self.tracking_calls.append(tracking_token)
        return self.tracking_order


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
            "delivery_latitude": 6.2542,
            "delivery_longitude": -75.5812,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == 15
    assert data["data"]["tracking_token"] == "a" * 43
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
            "idempotency_key": None,
            "delivery_latitude": 6.2542,
            "delivery_longitude": -75.5812,
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



def test_create_order_forwards_idempotency_key(
    monkeypatch,
):
    app = _create_app(monkeypatch)
    client = app.test_client()

    request_key = str(uuid4())

    response = client.post(
        "/api/orders",
        headers={
            "Idempotency-Key": request_key,
        },
        json={
            "name": "María López",
            "phone": "3001234567",
            "city": "Medellín",
            "address": "Calle 10 # 25-30",
            "observations": None,
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 201

    service = app.extensions[
        "_test_order_service"
    ]

    assert len(service.create_calls) == 1
    assert service.create_calls[0]["idempotency_key"] == request_key


def test_public_order_tracking_returns_only_safe_status_data(
    monkeypatch,
):
    app = _create_app(monkeypatch)
    client = app.test_client()

    tracking_token = "a" * 43

    service = app.extensions["_test_order_service"]

    service.tracking_order = SimpleNamespace(
        id=15,
        status="confirmed",
        created_at=datetime(
            2026, 10, 16, 10, 0, tzinfo=timezone.utc
        ),
        updated_at=datetime(
            2026, 10, 16, 11, 0, tzinfo=timezone.utc
        ),
        customer_name="Cliente Privado",
        phone="3001234567",
        address="Dirección privada",
        observations="Observación privada",
        status_history=[
            SimpleNamespace(
                previous_status="pending",
                new_status="pending",
                changed_at=datetime(
                    2026, 10, 16, 10, 0,
                    tzinfo=timezone.utc,
                ),
            ),
            SimpleNamespace(
                previous_status="pending",
                new_status="confirmed",
                changed_at=datetime(
                    2026, 10, 16, 11, 0,
                    tzinfo=timezone.utc,
                ),
            ),
        ],
    )

    response = client.post(
        "/api/orders/track",
        json={
            "tracking_token": tracking_token,
        },
    )

    assert response.status_code == 200

    body = response.get_json()
    assert body["success"] is True

    data = body["data"]

    assert data["id"] == 15
    assert data["status"] == "confirmed"
    assert len(data["status_history"]) == 2

    assert set(data) == {
        "id",
        "status",
        "created_at",
        "updated_at",
        "status_history",
    }

    serialized = response.get_data(as_text=True)

    assert "Cliente Privado" not in serialized
    assert "3001234567" not in serialized
    assert "Dirección privada" not in serialized
    assert "Observación privada" not in serialized

    assert service.tracking_calls == [
        tracking_token
    ]


def test_public_order_tracking_returns_generic_not_found(
    monkeypatch,
):
    app = _create_app(monkeypatch)
    client = app.test_client()

    response = client.post(
        "/api/orders/track",
        json={
            "tracking_token": "z" * 43,
        },
    )

    assert response.status_code == 404

    body = response.get_json()

    assert body["success"] is False
    assert body["error"]["code"] == (
        "ORDER_TRACKING_NOT_FOUND"
    )
