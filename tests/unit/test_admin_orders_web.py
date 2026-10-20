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


def test_admin_orders_page_keeps_whatsapp_module_upcoming_in_navigation(
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

def test_admin_orders_page_includes_order_status_actions(
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
        'id="admin-order-status-actions"'
        in body
    )

    assert (
        'id="admin-order-confirm-button"'
        in body
    )

    assert (
        'id="admin-order-cancel-button"'
        in body
    )

    assert (
        "Confirmar pedido"
        in body
    )

    assert (
        "Cancelar pedido"
        in body
    )


def test_admin_orders_page_loads_status_update_script(
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
        '/static/js/admin-orders.js'
        in body
    )


def test_admin_orders_page_keeps_whatsapp_separate_from_status_actions(
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
        "WhatsApp"
        in body
    )

    assert (
        "Próximo"
        in body
    )

    assert (
        "admin-order-confirm-button"
        in body
    )

    assert (
        "admin-order-cancel-button"
        in body
    )

def test_admin_orders_page_includes_customer_whatsapp_action(
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
        'id="admin-order-whatsapp-button"'
        in body
    )

    assert (
        "Contactar por WhatsApp"
        in body
    )

    assert (
        'id="admin-order-tracking-token"'
        in body
    )

    assert (
        'id="admin-order-tracking-copy-button"'
        in body
    )

    assert (
        'id="admin-order-tracking-whatsapp-button"'
        in body
    )

    assert (
        "Copiar código"
        in body
    )

    assert (
        "Compartir seguimiento por WhatsApp"
        in body
    )


def test_admin_orders_whatsapp_uses_customer_phone_not_business_number(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "normalizeAdminCustomerWhatsAppNumber"
        in body
    )

    assert (
        "order.phone"
        in body
    )

    assert (
        "https://wa.me/"
        in body
    )

    assert (
        "WHATSAPP_NUMBER"
        not in body
    )


def test_admin_orders_whatsapp_message_contains_customer_order_data(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "buildAdminCustomerWhatsAppMessage"
        in body
    )

    assert (
        "order.name"
        in body
    )

    assert (
        "order.city"
        in body
    )

    assert (
        "order.address"
        in body
    )

    assert (
        "order.observations"
        in body
    )

    assert (
        "order.items"
        in body
    )

    assert (
        "order.total"
        in body
    )


def test_admin_orders_page_keeps_status_actions_separate_from_customer_whatsapp(
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
        'id="admin-order-confirm-button"'
        in body
    )

    assert (
        'id="admin-order-cancel-button"'
        in body
    )

    assert (
        'id="admin-order-whatsapp-button"'
        in body
    )

    assert (
        "Confirmar pedido"
        in body
    )

    assert (
        "Cancelar pedido"
        in body
    )

    assert (
        "Contactar por WhatsApp"
        in body
    )

def test_admin_orders_page_supports_opening_order_from_query_string(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "function openOrderFromQueryString("
        in normalized_body
    )

    assert (
        "new URLSearchParams("
        in normalized_body
    )

    assert (
        'params.get(\n'
        in normalized_body
    )

    assert (
        '"order_id"'
        in normalized_body
    )

    assert (
        "openOrderDetail("
        in normalized_body
    )


def test_admin_orders_page_validates_order_id_query_parameter(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "!/^\\d+$/.test("
        in normalized_body
    )

    assert (
        "Number.isSafeInteger("
        in normalized_body
    )

    assert (
        "numericOrderId <= 0"
        in normalized_body
    )

def test_admin_orders_supports_status_filter_from_query_string(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "function applyOrderFiltersFromQueryString("
        in normalized_body
    )

    assert (
        "new URLSearchParams("
        in normalized_body
    )

    assert (
        'params.get(\n'
        in normalized_body
    )

    assert (
        '"status"'
        in normalized_body
    )

    assert (
        '"pending"'
        in normalized_body
    )

    assert (
        '"confirmed"'
        in normalized_body
    )

    assert (
        '"cancelled"'
        in normalized_body
    )

    assert (
        'statusSelect.value ='
        in normalized_body
    )


def test_admin_orders_initializes_query_filters_before_loading_orders(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "applyOrderFiltersFromQueryString();"
        in normalized_body
    )

    initialize_index = (
        normalized_body.index(
            "function initializeAdminOrders()"
        )
    )

    apply_index = (
        normalized_body.index(
            "applyOrderFiltersFromQueryString();",
            initialize_index,
        )
    )

    load_index = (
        normalized_body.index(
            "loadOrders();",
            initialize_index,
        )
    )

    assert (
        apply_index < load_index
    )

def test_admin_orders_page_includes_status_history_section(
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
        "Historial del pedido"
        in body
    )

    assert (
        'id="admin-order-status-history"'
        in body
    )

def test_admin_orders_renders_status_history_from_order_detail(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "function renderOrderStatusHistory("
        in normalized_body
    )

    assert (
        "order.status_history"
        in normalized_body
    )

    assert (
        "previous_status"
        in normalized_body
    )

    assert (
        "new_status"
        in normalized_body
    )

    assert (
        "changed_at"
        in normalized_body
    )

    assert (
        "getStatusLabel("
        in normalized_body
    )

    assert (
        "formatDate("
        in normalized_body
    )

def test_admin_orders_status_history_shows_most_recent_first(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "[...history].reverse()"
        in normalized_body
    )

    assert (
        "admin-orders-status-history__item--last"
        in normalized_body
    )


def test_admin_orders_configures_auto_refresh(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "autoRefreshEnabled"
        in normalized_body
    )

    assert (
        "autoRefreshTimer"
        in normalized_body
    )

    assert (
        "requestInFlight"
        in normalized_body
    )

    assert (
        "function setupAdminOrdersAutoRefresh("
        in normalized_body
    )

    assert (
        "window.setInterval("
        in normalized_body
    )

    assert (
        "document.visibilityState"
        in normalized_body
    )

    assert (
        "visibilitychange"
        in normalized_body
    )


def test_admin_orders_uses_silent_refresh_for_auto_update(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    assert (
        "loadOrders(\n"
        in normalized_body
    )

    assert (
        "silent: true"
        in normalized_body
    )

    assert (
        "Una actualización automática no debe borrar"
        in normalized_body
    )


def test_admin_orders_initializes_auto_refresh(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
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

    initialize_index = (
        normalized_body.index(
            "function initializeAdminOrders()"
        )
    )

    load_index = (
        normalized_body.index(
            "void loadOrders();",
            initialize_index,
        )
    )

    refresh_index = (
        normalized_body.index(
            "setupAdminOrdersAutoRefresh();",
            initialize_index,
        )
    )

    assert (
        load_index <
        refresh_index
    )


def test_admin_orders_page_includes_new_pending_orders_notice(
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
        'id="admin-orders-new-pending-notice"'
        in body
    )

    assert (
        'id="admin-orders-new-pending-notice-message"'
        in body
    )

    assert (
        'id="admin-orders-new-pending-notice-dismiss"'
        in body
    )

    assert (
        'href="/admin/orders?status=pending"'
        in body
    )

    assert (
        "Ver pedidos pendientes"
        in body
    )


def test_admin_orders_checks_pending_count_without_changing_polling_interval(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
        body
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    assert (
        "async function checkForNewPendingOrders("
        in normalized_body
    )

    assert (
        "/api/admin/orders?page=1&per_page=1&status=pending"
        in normalized_body
    )

    assert (
        "observeAdminOrdersPendingCount("
        in normalized_body
    )

    assert (
        "pendingCountRequestInFlight"
        in normalized_body
    )

    assert (
        "void checkForNewPendingOrders();"
        in normalized_body
    )

    assert (
        "ADMIN_DATA_REFRESH_INTERVAL_MS"
        in normalized_body
    )


def test_admin_orders_pending_notice_can_be_dismissed(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    normalized_body = (
        body
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    assert (
        "function dismissAdminOrdersNewPendingNotice("
        in normalized_body
    )

    assert (
        "adminOrdersState.unseenNewPendingCount = 0;"
        in normalized_body
    )

    assert (
        "function setupAdminOrdersNewPendingNotice("
        in normalized_body
    )

    assert (
        'getOrdersElement(\n            "admin-orders-new-pending-notice-dismiss"'
        in normalized_body
    )



def test_admin_order_detail_modal_supports_keyboard_focus_management(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[_admin_user()],
    )

    client = app.test_client()

    page_response = client.get("/admin/orders")
    assert page_response.status_code == 200

    page_body = page_response.get_data(as_text=True)

    assert 'role="dialog" aria-modal="true"' in page_body
    assert 'tabindex="-1"' in page_body

    script_response = client.get(
        "/static/js/admin-orders.js"
    )
    assert script_response.status_code == 200

    script_body = script_response.get_data(as_text=True)

    assert "getOrderDetailFocusableElements" in script_body
    assert "restoreOrderDetailFocus" in script_body
    assert "handleOrderDetailModalKeydown" in script_body
    assert 'event.key === "Escape"' in script_body
    assert 'event.key !== "Tab"' in script_body
    assert "detailFocusReturnElement" in script_body



def test_admin_orders_displays_pending_age_indicators(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[_admin_user()],
    )

    client = app.test_client()

    script_response = client.get(
        "/static/js/admin-orders.js"
    )

    assert script_response.status_code == 200

    script = script_response.get_data(
        as_text=True
    )

    assert "function getPendingAgePresentation(" in script
    assert "order.created_at" in script
    assert 'order.status === "pending"' in script
    assert 'elapsedMinutes >= 240' in script
    assert 'elapsedMinutes >= 60' in script
    assert "admin-orders-pending-age--${pendingAge.tone}" in script

    css_response = client.get(
        "/static/css/admin-orders.css"
    )

    assert css_response.status_code == 200

    css = css_response.get_data(
        as_text=True
    )

    assert ".admin-orders-pending-age--fresh" in css
    assert ".admin-orders-pending-age--attention" in css
    assert ".admin-orders-pending-age--urgent" in css



def test_admin_order_history_displays_relative_time_and_current_status(
    monkeypatch,
):
    app = _create_web_app(
        monkeypatch,
        users=[_admin_user()],
    )

    client = app.test_client()

    script_response = client.get(
        "/static/js/admin-orders.js"
    )

    assert script_response.status_code == 200

    script = script_response.get_data(
        as_text=True
    )

    assert "function formatRelativeTime(" in script
    assert "Intl.RelativeTimeFormat" in script
    assert "function renderOrderStatusHistory(" in script
    assert "latestEntry.new_status === currentStatus" in script
    assert "admin-orders-status-current-summary" in script
    assert "admin-orders-status-history__relative" in script
    assert "order.status_history" in script

    css_response = client.get(
        "/static/css/admin-orders.css"
    )

    assert css_response.status_code == 200

    css = css_response.get_data(
        as_text=True
    )

    assert ".admin-orders-status-current-summary" in css
    assert ".admin-orders-status-history__relative" in css


def test_admin_orders_js_includes_tracking_actions(
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
        "/static/js/admin-orders.js"
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert "getOrderTrackingToken" in body
    assert "copyOrderTrackingToken" in body
    assert "shareOrderTrackingByWhatsApp" in body
    assert "ORDER_TRACKING_TOKEN_PATTERN" in body
    assert "navigator.clipboard" in body
