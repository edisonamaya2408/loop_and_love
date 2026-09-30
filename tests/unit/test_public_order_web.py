import re

from app import create_app


def _create_web_app(
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

    monkeypatch.setenv(
        "ADMIN_SETUP_TOKEN",
        "A" * 40,
    )

    app = create_app(
        "development"
    )

    app.config[
        "WHATSAPP_NUMBER"
    ] = "573001234567"

    return app


def test_public_catalog_order_form_markup_is_available(
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
        'data-whatsapp-number="573001234567"'
        in body
    )

    assert (
        'id="catalog-order-form"'
        in body
    )

    assert (
        'id="order-customer-name"'
        in body
    )

    assert (
        'id="order-customer-phone"'
        in body
    )

    assert (
        'id="order-customer-city"'
        in body
    )

    assert (
        'id="order-customer-observations"'
        in body
    )

    assert (
        'id="order-submit"'
        in body
    )

    assert (
        "Enviar pedido por WhatsApp"
        in body
    )


def test_order_feedback_is_outside_cart_list(
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

    cart_list_start = body.find(
        'id="cart-list"'
    )

    cart_list_end = body.find(
        'id="order-feedback"'
    )

    assert cart_list_start != -1
    assert cart_list_end != -1

    assert (
        cart_list_end >
        cart_list_start
    )

    cart_list_fragment = body[
        cart_list_start:
        cart_list_end
    ]

    assert (
        'id="order-feedback"'
        not in cart_list_fragment
    )


def test_public_catalog_order_form_stylesheet_is_loaded(
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
        "/static/css/order.css"
        in body
    )


def test_public_catalog_order_javascript_is_loaded(
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
        "/static/js/order.js"
        in body
    )


def test_public_catalog_order_javascript_is_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/static/js/order.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        '"/api/orders"'
        in body
    )

    assert (
        "getOrderCartItems"
        in body
    )

    assert (
        "getWhatsAppNumber"
        in body
    )

    assert (
        "buildWhatsAppMessage"
        in body
    )

    assert (
        "buildWhatsAppUrl"
        in body
    )

    assert (
        "https://wa.me/"
        in body
    )

    assert (
        "window.open"
        in body
    )

    assert re.search(
        r'window\.open\(\s*""\s*,\s*"_blank"\s*\)',
        body,
    )

    assert (
        "noopener,noreferrer"
        not in body
    )

    assert (
        "whatsappWindow.location.replace"
        in body
    )

    assert (
        "clearCart"
        in body
    )
    

def test_public_catalog_order_styles_are_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/static/css/order.css"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        ".catalog-order-request"
        in body
    )

    assert (
        ".catalog-order-form"
        in body
    )

    assert (
        ".catalog-order-feedback"
        in body
    )

    assert (
        ".catalog-order-form__submit"
        in body
    )