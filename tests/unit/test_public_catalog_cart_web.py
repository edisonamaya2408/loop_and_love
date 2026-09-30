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

    def create(
        self,
        admin_user,
    ):
        admin_user.id = (
            len(self.users) + 1
        )

        self.users.append(
            admin_user
        )

        return admin_user

    def increment_token_version(
        self,
        user_id,
    ):
        user = self.get_by_id(
            user_id
        )

        if user is None:
            return None

        user.token_version += 1

        return user


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


def test_public_catalog_cart_markup_is_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="pedido"'
        in body
    )

    assert (
        'id="cart-count"'
        in body
    )

    assert (
        'id="cart-section-count"'
        in body
    )

    assert (
        'id="cart-empty"'
        in body
    )

    assert (
        'id="cart-list"'
        in body
    )

    assert (
        'id="cart-items"'
        in body
    )

    assert (
        'id="cart-total"'
        in body
    )

    assert (
        'id="cart-clear"'
        in body
    )


def test_public_catalog_cart_stylesheet_is_loaded(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "/static/css/cart.css"
        in body
    )


def test_public_catalog_cart_javascript_is_loaded(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        '/static/js/cart.js'
        in body
    )


def test_public_catalog_cart_javascript_is_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/static/js/cart.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "loop_and_love.b2b_cart"
        in body
    )

    assert (
        "addProductToCart"
        in body
    )

    assert (
        "updateCartQuantity"
        in body
    )

    assert (
        "removeCartItem"
        in body
    )

    assert (
        "clearCart"
        in body
    )

    assert (
        "setupProductCardObserver"
        in body
    )


def test_public_catalog_cart_styles_are_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/static/css/cart.css"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        ".catalog-cart-item"
        in body
    )

    assert (
        ".catalog-product-card__add"
        in body
    )

    assert (
        ".catalog-cart-summary"
        in body
    )


def test_public_catalog_cart_keeps_admin_separation(
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
        "/"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "admin-sidebar"
        not in body
    )

    assert (
        "Cerrar sesión"
        not in body
    )

    assert (
        "Administrador"
        not in body
    )


def test_public_catalog_cart_keeps_image_viewer(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="catalog-image-modal"'
        in body
    )

    assert (
        'id="catalog-image-modal-image"'
        in body
    )

    assert (
        'id="catalog-image-modal-close"'
        in body
    )