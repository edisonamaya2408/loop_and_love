from app import create_app

from app.domain.entities.admin_user import (
    AdminUserEntity,
)


class FakeAdminUserRepository:
    def __init__(
        self,
        users=None,
    ):
        self.users = list(
            users or []
        )

    def count(self):
        return len(
            self.users
        )

    def get_by_id(
        self,
        user_id,
    ):
        for user in self.users:
            if user.id == user_id:
                return user

        return None

    def get_by_email(
        self,
        email,
    ):
        for user in self.users:
            if user.email == email:
                return user
        return None


def _create_web_app(
    monkeypatch,
    users=None,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setenv(
        "ADMIN_SETUP_TOKEN",
        "A" * 40,
    )

    app = create_app(
        "development"
    )

    repository = (
        FakeAdminUserRepository(
            users=users
        )
    )

    app.extensions[
        "admin_user_repository"
    ] = repository

    return app


def _admin_user():
    return AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )


def test_admin_orders_page_redirects_to_setup_when_no_admin_exists(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/setup"
    )


def test_admin_orders_page_renders_when_admin_exists(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Pedidos"
        in body
    )

    assert (
        "GESTIÓN DE PEDIDOS"
        in body
    )

    assert (
        'id="admin-orders-search"'
        in body
    )

    assert (
        'id="admin-orders-status"'
        in body
    )

    assert (
        'id="admin-orders-table-body"'
        in body
    )

    assert (
        'id="admin-orders-pagination"'
        in body
    )

    assert (
        "/static/css/admin-orders.css"
        in body
    )

    assert (
        "/static/js/admin-orders.js"
        in body
    )


def test_admin_orders_page_navigation_marks_orders_as_active(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "admin-nav__item--active"
        in body
    )


def test_admin_orders_page_keeps_other_admin_navigation(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Dashboard"
        in body
    )

    assert (
        "Productos"
        in body
    )

    assert (
        "Categorías"
        in body
    )

    assert (
        "Usuarios"
        in body
    )

    assert (
        "Ver portal B2B"
        in body
    )

    assert (
        "Cerrar sesión"
        in body
    )


def test_admin_orders_page_keeps_whatsapp_as_upcoming_feature(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "admin-orders"
        in body
    )

    assert (
        "WhatsApp"
        in body
    )

    assert (
        "Próximo"
        in body
    )

def test_admin_orders_page_includes_order_detail_modal(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="admin-order-detail-modal"'
        in body
    )

    assert (
        'id="admin-order-detail-close"'
        in body
    )

    assert (
        'id="admin-order-detail-loading"'
        in body
    )

    assert (
        'id="admin-order-detail-message"'
        in body
    )

    assert (
        'id="admin-order-detail-content"'
        in body
    )

    assert (
        'id="admin-order-detail-items"'
        in body
    )


def test_admin_orders_page_includes_detail_styles_and_script(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/orders"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "/static/css/admin-orders.css"
        in body
    )

    assert (
        "/static/js/admin-orders.js"
        in body
    )
