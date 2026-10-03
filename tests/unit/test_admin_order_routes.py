from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app import create_app


class FakeAdminUserRepository:
    def __init__(
        self,
        users=None,
    ):
        self.users = list(
            users or []
        )

    def get_by_id(
        self,
        user_id,
    ):
        for user in self.users:
            if user.id == user_id:
                return user

        return None


class FakeOrderService:
    def __init__(
        self,
    ):
        self.list_calls = []

        self.orders = [
            SimpleNamespace(
                id=15,
                customer_name="María López",
                phone="+57 300 123 4567",
                city="Medellín",
                address="Calle 10 # 25-30",
                observations="Entregar mañana.",
                status="pending",
                items=[
                    SimpleNamespace(
                        product_id=1,
                        product_code="LL-001",
                        product_name="Amigurumi Oso",
                        unit_price=Decimal(
                            "85000.00"
                        ),
                        quantity=2,
                        line_total=Decimal(
                            "170000.00"
                        ),
                    )
                ],
                total=Decimal(
                    "170000.00"
                ),
                created_at=datetime(
                    2026,
                    9,
                    29,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
                updated_at=datetime(
                    2026,
                    9,
                    29,
                    20,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
            SimpleNamespace(
                id=14,
                customer_name="Carlos Gómez",
                phone="3009876543",
                city="Bogotá",
                address="Carrera 15 # 80-20",
                observations=None,
                status="confirmed",
                items=[
                    SimpleNamespace(
                        product_id=2,
                        product_code="LL-002",
                        product_name="Amigurumi Gato",
                        unit_price=Decimal(
                            "90000.00"
                        ),
                        quantity=1,
                        line_total=Decimal(
                            "90000.00"
                        ),
                    )
                ],
                total=Decimal(
                    "90000.00"
                ),
                created_at=datetime(
                    2026,
                    9,
                    28,
                    18,
                    0,
                    tzinfo=timezone.utc,
                ),
                updated_at=datetime(
                    2026,
                    9,
                    28,
                    18,
                    0,
                    tzinfo=timezone.utc,
                ),
            ),
        ]

    def get_order(
        self,
        order_id,
    ):
        for order in self.orders:
            if order.id == order_id:
                return order

        return None

    def list_admin_orders(
        self,
        search=None,
        status=None,
        page=None,
        per_page=None,
    ):
        self.list_calls.append(
            {
                "search": search,
                "status": status,
                "page": page,
                "per_page": per_page,
            }
        )

        page = int(
            page or 1
        )

        per_page = int(
            per_page or 12
        )

        class Pagination:
            pass

        pagination = Pagination()

        pagination.page = page
        pagination.per_page = per_page
        pagination.total = len(
            self.orders
        )
        pagination.pages = (
            (
                len(self.orders)
                + per_page
                - 1
            )
            // per_page
            if self.orders
            else 0
        )
        pagination.has_next = (
            page < pagination.pages
        )
        pagination.has_previous = (
            page > 1
        )

        class Result:
            pass

        result = Result()

        result.items = self.orders[
            (page - 1) * per_page:
            page * per_page
        ]

        result.pagination = pagination

        return result

    def update_admin_order_status(
        self,
        order_id,
        status,
    ):
        allowed_statuses = {
            "confirmed",
            "cancelled",
        }

        if status not in allowed_statuses:
            raise ValueError(
                "El estado solicitado no es válido."
            )

        order = self.get_order(
            order_id
        )

        if order is None:
            return None

        if order.status == status:
            raise ValueError(
                "El pedido ya tiene ese estado."
            )

        order.status = status

        return order


def _admin():
    return SimpleNamespace(
        id=1,
        email="admin@test.com",
        is_active=True,
        token_version=0,
    )


def _auth_headers():
    return {
        "Authorization": "Bearer test-token",
    }


def _configure_valid_jwt(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.infrastructure.security.jwt_service.JWTService.decode_access_token",
        lambda token: {
            "sub": "1",
            "email": "admin@test.com",
            "token_version": 0,
        },
    )


def _configure_invalid_jwt(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.infrastructure.security.jwt_service.JWTService.decode_access_token",
        lambda token: (
            (_ for _ in ()).throw(
                ValueError(
                    "invalid token"
                )
            )
        ),
    )


def _create_test_app(
    monkeypatch,
):
    app = create_app(
        "development"
    )

    order_service = (
        FakeOrderService()
    )

    admin_user_repository = (
        FakeAdminUserRepository(
            users=[
                _admin()
            ]
        )
    )

    app.extensions[
        "admin_user_repository"
    ] = admin_user_repository

    monkeypatch.setattr(
        "app.presentation.routes.admin_order_routes._get_order_service",
        lambda: order_service,
    )

    return (
        app,
        order_service,
    )


def test_list_admin_orders_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "AUTHENTICATION_REQUIRED"
    )


def test_list_admin_orders_returns_orders_with_pagination(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert len(
        data["data"]
    ) == 2

    assert data["pagination"] == {
        "page": 1,
        "per_page": 12,
        "total": 2,
        "pages": 1,
        "has_next": False,
        "has_previous": False,
    }

    first_order = data[
        "data"
    ][0]

    assert first_order["id"] == 15

    assert first_order["name"] == (
        "María López"
    )

    assert first_order["phone"] == (
        "+57 300 123 4567"
    )

    assert first_order["city"] == (
        "Medellín"
    )

    assert first_order["address"] == (
        "Calle 10 # 25-30"
    )

    assert first_order[
        "observations"
    ] == "Entregar mañana."

    assert first_order["status"] == (
        "pending"
    )

    assert first_order["items"] == [
        {
            "product_id": 1,
            "code": "LL-001",
            "name": "Amigurumi Oso",
            "unit_price": "85000.00",
            "quantity": 2,
            "line_total": "170000.00",
        }
    ]

    assert first_order[
        "total"
    ] == "170000.00"

    assert first_order[
        "created_at"
    ] == "2026-09-29T20:00:00+00:00"

    assert first_order[
        "updated_at"
    ] == "2026-09-29T20:00:00+00:00"


def test_list_admin_orders_passes_filters_and_pagination_to_service(
    monkeypatch,
):
    app, order_service = (
        _create_test_app(
            monkeypatch
        )
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders",
        query_string={
            "search": "María",
            "status": "pending",
            "page": "2",
            "per_page": "5",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    assert order_service.list_calls == [
        {
            "search": "María",
            "status": "pending",
            "page": "2",
            "per_page": "5",
        }
    ]


def test_list_admin_orders_handles_empty_results(
    monkeypatch,
):
    app, order_service = (
        _create_test_app(
            monkeypatch
        )
    )

    order_service.orders = []

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"] == []

    assert data["pagination"] == {
        "page": 1,
        "per_page": 12,
        "total": 0,
        "pages": 0,
        "has_next": False,
        "has_previous": False,
    }


def test_list_admin_orders_rejects_invalid_token(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_invalid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders",
        headers=_auth_headers(),
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "INVALID_OR_EXPIRED_TOKEN"
    )


def test_get_admin_order_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders/15"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "AUTHENTICATION_REQUIRED"
    )


def test_get_admin_order_returns_order(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders/15",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    order = data["data"]

    assert order["id"] == 15

    assert order["name"] == (
        "María López"
    )

    assert order["phone"] == (
        "+57 300 123 4567"
    )

    assert order["city"] == (
        "Medellín"
    )

    assert order["address"] == (
        "Calle 10 # 25-30"
    )

    assert order["observations"] == (
        "Entregar mañana."
    )

    assert order["status"] == (
        "pending"
    )

    assert order["items"] == [
        {
            "product_id": 1,
            "code": "LL-001",
            "name": "Amigurumi Oso",
            "unit_price": "85000.00",
            "quantity": 2,
            "line_total": "170000.00",
        }
    ]

    assert order["total"] == (
        "170000.00"
    )


def test_get_admin_order_returns_not_found(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/orders/999",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "ORDER_NOT_FOUND"
    )

    assert data["error"]["message"] == (
        "El pedido no existe."
    )

def test_update_admin_order_status_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/orders/15/status",
        json={
            "status": "confirmed"
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "AUTHENTICATION_REQUIRED"
    )


def test_update_admin_order_status_confirms_order(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/orders/15/status",
        json={
            "status": "confirmed"
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["id"] == 15

    assert data["data"]["status"] == (
        "confirmed"
    )


def test_update_admin_order_status_cancels_order(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/orders/15/status",
        json={
            "status": "cancelled"
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["status"] == (
        "cancelled"
    )


def test_update_admin_order_status_returns_not_found(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/orders/999/status",
        json={
            "status": "confirmed"
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "ORDER_NOT_FOUND"
    )


def test_update_admin_order_status_rejects_invalid_payload(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/orders/15/status",
        json={
            "status": "invalid"
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "INVALID_ORDER_STATUS"
    )