import re


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


def _normalize_css(
    body,
):
    return (
        body
        .replace(
            "\r\n",
            "\n",
        )
        .replace(
            "\r",
            "\n",
        )
    )


def _normalize_css_whitespace(
    body,
):
    return " ".join(
        _normalize_css(
            body
        ).split()
    )


def _get_css_block(
    body,
    selector,
    end_selector,
):
    css = _normalize_css(
        body
    )

    start = css.find(
        selector
    )

    assert start != -1

    end = css.find(
        end_selector,
        start,
    )

    assert end != -1

    return css[
        start:end
    ]


def _has_declaration(
    css_block,
    property_name,
    value,
):
    normalized = _normalize_css_whitespace(
        css_block
    )

    pattern = (
        rf"(?<![\w-])"
        rf"{re.escape(property_name)}"
        rf"\s*:\s*"
        rf"{re.escape(value)}"
        rf"\s*;"
    )

    return re.search(
        pattern,
        normalized,
    ) is not None


def _does_not_have_exact_declaration(
    css_block,
    property_name,
    value,
):
    return not _has_declaration(
        css_block,
        property_name,
        value,
    )


def test_public_catalog_has_functional_catalog_elements(
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
        'id="catalog-filter-form"'
        in body
    )

    assert (
        'id="catalog-search"'
        in body
    )

    assert (
        'id="catalog-category"'
        in body
    )

    assert (
        'id="catalog-min-price"'
        in body
    )

    assert (
        'id="catalog-max-price"'
        in body
    )

    assert (
        'id="catalog-results"'
        in body
    )

    assert (
        'id="catalog-pagination"'
        in body
    )

    assert (
        'id="catalog-retry"'
        in body
    )


def test_public_catalog_loads_catalog_javascript_and_stylesheet(
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
        "/static/js/app.js"
        in body
    )

    assert (
        "/static/css/public.css"
        in body
    )

    assert (
        "/static/css/catalog.css"
        in body
    )


def test_public_catalog_does_not_render_admin_interface(
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
        "Dashboard"
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


def test_public_catalog_no_longer_shows_placeholder_message(
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
        "Próximamente conectado"
        not in body
    )

    assert (
        "Estamos preparando tu catálogo"
        not in body
    )


def test_public_catalog_keeps_order_section(
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
        "Mi pedido"
        in body
    )

    assert (
        "Agrega los productos que deseas solicitar."
        in body
    )

    assert (
        "El pedido se conserva en este navegador"
        in body
    )


def test_public_catalog_includes_product_image_viewer(
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

    assert (
        "data-catalog-image-modal-close"
        in body
    )


def test_public_catalog_image_viewer_assets_are_available(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    javascript_response = client.get(
        "/static/js/app.js"
    )


    assert (
        javascript_response.status_code
        == 200
    )


    javascript_body = (
        javascript_response.get_data(
            as_text=True
        )
    )


    assert (
        "openCatalogImageModal"
        in javascript_body
    )


    css_response = client.get(
        "/static/css/catalog.css"
    )


    assert (
        css_response.status_code
        == 200
    )


    css_body = (
        css_response.get_data(
            as_text=True
        )
    )


    assert (
        ".catalog-image-modal"
        in css_body
    )


    assert (
        "object-fit:"
        in css_body
    )


    assert (
        "contain"
        in css_body
    )


def test_public_catalog_card_image_fits_inside_fixed_4_3_frame(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/css/catalog.css"
    )


    assert response.status_code == 200


    body = response.get_data(
        as_text=True
    )


    frame_styles = _get_css_block(
        body,
        ".catalog-product-card__media {",
        ".catalog-product-card__media:focus-visible",
    )


    image_styles = _get_css_block(
        body,
        ".catalog-product-card__media img {",
        ".catalog-product-card:hover",
    )


    assert _has_declaration(
        frame_styles,
        "aspect-ratio",
        "4 / 3",
    )


    assert _has_declaration(
        image_styles,
        "width",
        "auto",
    )


    assert _has_declaration(
        image_styles,
        "height",
        "auto",
    )


    assert _has_declaration(
        image_styles,
        "max-width",
        "100%",
    )


    assert _has_declaration(
        image_styles,
        "max-height",
        "100%",
    )


    assert _has_declaration(
        image_styles,
        "object-fit",
        "contain",
    )


def test_public_catalog_card_image_does_not_force_full_height_or_width(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/css/catalog.css"
    )


    assert response.status_code == 200


    body = response.get_data(
        as_text=True
    )


    image_styles = _get_css_block(
        body,
        ".catalog-product-card__media img {",
        ".catalog-product-card:hover",
    )


    assert _does_not_have_exact_declaration(
        image_styles,
        "width",
        "100%",
    )


    assert _does_not_have_exact_declaration(
        image_styles,
        "height",
        "100%",
    )


def test_public_catalog_modal_image_uses_intrinsic_dimensions_inside_viewer(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/css/catalog.css"
    )


    assert response.status_code == 200


    body = response.get_data(
        as_text=True
    )


    image_styles = _get_css_block(
        body,
        ".catalog-image-modal__image {",
        ".catalog-image-modal__hint",
    )


    assert _has_declaration(
        image_styles,
        "width",
        "auto",
    )


    assert _has_declaration(
        image_styles,
        "height",
        "auto",
    )


    assert _has_declaration(
        image_styles,
        "max-width",
        "100%",
    )


    assert _has_declaration(
        image_styles,
        "max-height",
        "100%",
    )


    assert _has_declaration(
        image_styles,
        "object-fit",
        "contain",
    )


def test_public_catalog_modal_image_does_not_force_full_height_or_width(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/css/catalog.css"
    )


    assert response.status_code == 200


    body = response.get_data(
        as_text=True
    )


    image_styles = _get_css_block(
        body,
        ".catalog-image-modal__image {",
        ".catalog-image-modal__hint",
    )


    assert _does_not_have_exact_declaration(
        image_styles,
        "width",
        "100%",
    )


    assert _does_not_have_exact_declaration(
        image_styles,
        "height",
        "100%",
    )


def test_public_catalog_modal_keeps_viewer_dimensions_constrained(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/css/catalog.css"
    )


    assert response.status_code == 200


    body = _normalize_css(
        response.get_data(
            as_text=True
        )
    )


    modal_start = body.find(
        ".catalog-image-modal__dialog {"
    )


    body_start = body.find(
        ".catalog-image-modal__body {",
        modal_start,
    )


    image_start = body.find(
        ".catalog-image-modal__image {",
        body_start,
    )


    assert modal_start != -1
    assert body_start != -1
    assert image_start != -1


    modal_styles = body[
        modal_start:body_start
    ]


    body_styles = body[
        body_start:image_start
    ]


    assert _has_declaration(
        modal_styles,
        "height",
        "min(88vh, 820px)",
    )


    assert _has_declaration(
        modal_styles,
        "overflow",
        "hidden",
    )


    assert _has_declaration(
        body_styles,
        "width",
        "100%",
    )


    assert _has_declaration(
        body_styles,
        "height",
        "100%",
    )


    assert _has_declaration(
        body_styles,
        "overflow",
        "hidden",
    )


def test_public_catalog_keeps_product_image_viewer_javascript_behavior(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    response = client.get(
        "/static/js/app.js"
    )


    assert response.status_code == 200


    javascript = response.get_data(
        as_text=True
    )


    assert (
        "function openCatalogImageModal"
        in javascript
    )


    assert (
        "image.src ="
        in javascript
    )


    assert (
        "modal.hidden ="
        in javascript
    )


    assert (
        "document.body.style.overflow ="
        in javascript
    )


def test_public_catalog_card_image_modal_remains_available_after_css_adjustment(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch
    )

    client = app.test_client()


    html_response = client.get(
        "/"
    )


    css_response = client.get(
        "/static/css/catalog.css"
    )


    javascript_response = client.get(
        "/static/js/app.js"
    )


    assert (
        html_response.status_code
        == 200
    )


    assert (
        css_response.status_code
        == 200
    )


    assert (
        javascript_response.status_code
        == 200
    )


    html = html_response.get_data(
        as_text=True
    )


    css = css_response.get_data(
        as_text=True
    )


    javascript = (
        javascript_response.get_data(
            as_text=True
        )
    )


    assert (
        'id="catalog-image-modal"'
        in html
    )


    assert (
        ".catalog-image-modal__image"
        in css
    )


    assert (
        "openCatalogImageModal"
        in javascript
    )



def test_public_catalog_image_modal_supports_keyboard_focus_management(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    html_response = client.get("/")
    js_response = client.get("/static/js/app.js")
    css_response = client.get("/static/css/catalog.css")

    assert html_response.status_code == 200
    assert js_response.status_code == 200
    assert css_response.status_code == 200

    html = html_response.get_data(as_text=True)
    javascript = js_response.get_data(as_text=True)
    css = css_response.get_data(as_text=True)

    assert 'aria-describedby="catalog-image-modal-hint"' in html
    assert 'tabindex="-1"' in html
    assert 'id="catalog-image-modal-hint"' in html

    assert "catalogImageModalState" in javascript
    assert "getCatalogImageModalFocusableElements" in javascript
    assert "handleCatalogImageModalKeydown" in javascript
    assert "event.key === \"Escape\"" in javascript
    assert "event.key !== \"Tab\"" in javascript
    assert "returnFocusElement.focus()" in javascript
    assert "previousBodyOverflow" in javascript

    assert ".catalog-product-card__media:focus-visible" in css
    assert ".catalog-image-modal__close:focus-visible" in css


def test_public_order_checkout_preserves_idempotency_on_retry(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    response = client.get("/static/js/order.js")

    assert response.status_code == 200

    script = response.get_data(as_text=True)

    assert 'const ORDER_ATTEMPT_STORAGE_KEY' in script
    assert "function fingerprintOrderPayload(" in script
    assert "function createOrderIdempotencyKey(" in script
    assert "function getOrderIdempotencyKey(" in script
    assert "function clearOrderIdempotencyAttempt(" in script
    assert '"Idempotency-Key": idempotencyKey' in script
    assert "clearOrderIdempotencyAttempt();" in script
    assert "IDEMPOTENCY_KEY_REUSED" in script
    assert '".catalog-product-card__add"' in script


def test_public_order_supports_safe_retry_and_result_summary(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    script_response = client.get(
        "/static/js/order.js"
    )

    css_response = client.get(
        "/static/css/order.css"
    )

    assert script_response.status_code == 200
    assert css_response.status_code == 200

    script = script_response.get_data(as_text=True)
    css = css_response.get_data(as_text=True)

    assert "pendingRetry: null" in script
    assert "blockedAttempt: null" in script
    assert "function readStoredOrderAttempt()" in script
    assert "function retryPendingOrder()" in script
    assert "function showUncertainOrderResult(" in script
    assert "function performOrderSubmission(" in script
    assert "Reintentar el mismo pedido" in script
    assert "orderState.pendingRetry" in script
    assert "IDEMPOTENCY_KEY_REUSED" in script

    assert "catalog-order-feedback__summary" in script
    assert "Resumen del pedido" in script
    assert "No pudimos confirmar la respuesta del servidor" in script

    assert ".catalog-order-feedback--warning" in css
    assert ".catalog-order-feedback--pending" in css
    assert ".catalog-order-feedback__summary" in css
    assert ".catalog-order-feedback__action" in css


def test_public_catalog_supports_order_tracking_ui(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    html_response = client.get("/")
    js_response = client.get("/static/js/order.js")
    css_response = client.get("/static/css/order.css")

    assert html_response.status_code == 200
    assert js_response.status_code == 200
    assert css_response.status_code == 200

    html = html_response.get_data(as_text=True)
    javascript = js_response.get_data(as_text=True)
    css = css_response.get_data(as_text=True)

    assert 'id="order-tracking-form"' in html
    assert 'id="order-tracking-token"' in html
    assert 'id="order-tracking-remember"' in html
    assert 'id="order-tracking-submit"' in html
    assert 'id="order-tracking-result"' in html

    assert "ORDER_TRACKING_SESSION_KEY" in javascript
    assert "ORDER_TRACKING_LOCAL_KEY" in javascript
    assert "function saveOrderTrackingToken(" in javascript
    assert "function readSavedOrderTrackingToken(" in javascript
    assert "function renderOrderTrackingResult(" in javascript
    assert "function loadOrderTracking(" in javascript
    assert '`${ORDER_API_URL}/track`' in javascript
    assert "setupCatalogOrderTracking();" in javascript
    assert "confirmedOrder.tracking_token" in javascript

    assert ".catalog-order-tracking__result" in css
    assert ".catalog-order-tracking__history" in css
    assert ".catalog-order-tracking__status--pending" in css
    assert ".catalog-order-tracking__status--confirmed" in css
    assert ".catalog-order-tracking__status--cancelled" in css


def test_public_catalog_feedbacks_auto_dismiss_and_tracking_guidance(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    js_response = client.get("/static/js/order.js")
    css_response = client.get("/static/css/order.css")

    assert js_response.status_code == 200
    assert css_response.status_code == 200

    javascript = js_response.get_data(as_text=True)
    css = css_response.get_data(as_text=True)

    # Los avisos temporales tienen sus propios temporizadores.
    assert "ORDER_FEEDBACK_AUTO_DISMISS_MS" in javascript
    assert "ORDER_TRACKING_FEEDBACK_AUTO_DISMISS_MS" in javascript
    assert "clearOrderFeedbackDismissTimer" in javascript
    assert "clearOrderTrackingFeedbackDismissTimer" in javascript
    assert "window.setTimeout" in javascript

    # El resumen y el enlace de WhatsApp no deben ocultarse
    # junto con el texto temporal de confirmación.
    assert "keepOrderDetails" in javascript
    assert "messageElement?.remove()" in javascript
    assert "type === \"pending\"" in javascript
    assert "hasAction" in javascript

    # Los estados conservan instrucciones visibles y una
    # acción de contacto independiente del aviso temporal.
    assert "function getOrderTrackingGuidance(" in javascript
    assert 'case "pending"' in javascript
    assert 'case "confirmed"' in javascript
    assert 'case "cancelled"' in javascript
    assert "function createOrderTrackingContactLink(" in javascript
    assert "catalog-order-tracking__guidance" in javascript

    assert ".catalog-order-tracking__guidance" in css
    assert ".catalog-order-tracking__contact" in css


def test_public_catalog_mobile_controls_are_touch_friendly(
    monkeypatch,
):
    app = _create_web_app(monkeypatch)
    client = app.test_client()

    resources = {
        "public": client.get("/static/css/public.css"),
        "catalog": client.get("/static/css/catalog.css"),
        "cart": client.get("/static/css/cart.css"),
        "order": client.get("/static/css/order.css"),
    }

    for name, response in resources.items():
        assert response.status_code == 200, name

    public_css = resources["public"].get_data(as_text=True)
    catalog_css = resources["catalog"].get_data(as_text=True)
    cart_css = resources["cart"].get_data(as_text=True)
    order_css = resources["order"].get_data(as_text=True)

    assert re.search(
        r"\.catalog-field input,\s*"
        r"\.catalog-field select\s*\{[^}]*"
        r"font-size:\s*16px;",
        public_css,
        re.S,
    )

    assert re.search(
        r"\.catalog-order-form input,\s*"
        r"\.catalog-order-form textarea,\s*"
        r"\.catalog-order-tracking__form "
        r"input\[type=\"text\"\]\s*\{[^}]*"
        r"font-size:\s*16px;",
        order_css,
        re.S,
    )

    assert re.search(
        r"\.catalog-cart-item__quantity-button\s*\{[^}]*"
        r"width:\s*44px;[^}]*height:\s*44px;",
        cart_css,
        re.S,
    )

    assert ".catalog-cart-item__remove:focus-visible" in cart_css
    assert ".catalog-product-card:hover" in catalog_css
    assert "@media (hover: none)" in catalog_css
    assert ".catalog-order-tracking__contact" in order_css