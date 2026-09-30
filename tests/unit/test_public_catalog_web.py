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