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

    return app, repository


def test_public_home_page_renders_public_portal(
    monkeypatch,
):
    app, _ = _create_web_app(
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
        "Encuentra"
        in body
    )

    assert (
        "Aplicar filtros"
        in body
    )

    assert (
        "Mi pedido"
        in body
    )

    assert (
        "Administrador"
        not in body
    )

    assert (
        "admin-sidebar"
        not in body
    )


def test_admin_redirects_to_setup_when_no_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/setup"
    )


def test_admin_redirects_to_login_when_admin_exists(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/login"
    )


def test_admin_setup_page_renders_when_no_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin/setup"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Crear administrador"
        in body
    )

    assert (
        "Código de configuración"
        in body
    )

    assert (
        'name="setup_token"'
        in body
    )

    assert (
        'name="email"'
        in body
    )

    assert (
        'name="password"'
        in body
    )


def test_admin_setup_redirects_to_login_after_setup_completed(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/setup"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/login"
    )


def test_admin_setup_creates_first_admin(
    monkeypatch,
):
    app, repository = (
        _create_web_app(
            monkeypatch
        )
    )

    client = app.test_client()

    response = client.post(
        "/admin/setup",
        data={
            "setup_token": "A" * 40,
            "name": "Administradora Inicial",
            "email": "Admin@Example.COM",
            "password": "Password123!",
            "password_confirmation": (
                "Password123!"
            ),
        },
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/login?created=1"
    )

    assert repository.count() == 1

    created = repository.get_by_id(
        1
    )

    assert created is not None
    assert created.name == "Administradora Inicial"
    assert created.email == "admin@example.com"
    assert created.is_active is True
    assert created.token_version == 0


def test_admin_setup_rejects_invalid_setup_token(
    monkeypatch,
):
    app, repository = (
        _create_web_app(
            monkeypatch
        )
    )

    client = app.test_client()

    response = client.post(
        "/admin/setup",
        data={
            "setup_token": "wrong",
            "email": "admin@example.com",
            "password": "Password123!",
            "password_confirmation": (
                "Password123!"
            ),
        },
    )

    assert response.status_code == 401

    assert (
        "código de configuración no es válido"
        in response.get_data(
            as_text=True
        )
    )

    assert repository.count() == 0


def test_admin_setup_rejects_when_admin_already_exists(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="existing@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, repository = (
        _create_web_app(
            monkeypatch,
            users=users,
        )
    )

    client = app.test_client()

    response = client.post(
        "/admin/setup",
        data={
            "setup_token": "A" * 40,
            "email": "new@example.com",
            "password": "Password123!",
            "password_confirmation": (
                "Password123!"
            ),
        },
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/login"
    )

    assert repository.count() == 1


def test_admin_login_redirects_to_setup_when_no_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin/login"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/setup"
    )


def test_admin_login_renders_when_admin_exists(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/login"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Administración"
        in body
    )

    assert (
        'id="admin-login-form"'
        in body
    )


def test_admin_dashboard_redirects_to_setup_when_no_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/setup"
    )


def test_admin_dashboard_renders_when_admin_exists(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
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
        "admin-sidebar"
        in body
    )


def test_admin_login_displays_setup_confirmation(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/login?created=1"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Administrador creado correctamente"
        in body
    )

def test_admin_dashboard_includes_live_order_kpis(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="admin-order-count"'
        in body
    )

    assert (
        'id="admin-pending-order-count"'
        in body
    )

    assert (
        'href="/admin/orders?status=pending"'
        in body
    )

    assert (
        "Pedidos registrados"
        in body
    )

    assert (
        "Pedidos pendientes de gestión"
        in body
    )

    assert (
        "Flujo B2B + WhatsApp"
        not in body
    )

    assert (
        "Pedidos desde catálogo"
        not in body
    )


def test_admin_dashboard_loads_dashboard_order_endpoints(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "/api/admin/orders?page=1&per_page=5"
        in body
    )

    assert (
        "/api/admin/orders?page=1&per_page=1&status=pending"
        in body
    )

    assert (
        "admin-order-count"
        in body
    )

    assert (
        "admin-pending-order-count"
        in body
    )

    assert (
        "Promise.allSettled"
        in body
    )

def test_admin_dashboard_includes_recent_orders_section(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Pedidos recientes"
        in body
    )

    assert (
        'id="admin-dashboard-orders-body"'
        in body
    )

    assert (
        'id="admin-dashboard-orders-loading"'
        in body
    )

    assert (
        'id="admin-dashboard-orders-empty"'
        in body
    )

    assert (
        "Ver todos los pedidos"
        in body
    )


def test_admin_dashboard_uses_recent_orders_endpoint(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
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
        "/api/admin/orders?page=1&per_page=5"
        in normalized_body
    )

    assert (
        "renderDashboardRecentOrders"
        in normalized_body
    )

    assert (
        "getDashboardOrderStatusLabel"
        in normalized_body
    )

    assert (
        "admin-dashboard-orders-body"
        in normalized_body
    )

    assert (
        "`/admin/orders?order_id=${encodeURIComponent("
        in normalized_body
    )

def test_admin_dashboard_defines_recent_order_currency_formatter(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
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
        "function formatDashboardCurrency("
        in normalized_body
    )

    assert (
        "formatDashboardCurrency("
        in normalized_body
    )

    assert (
        'currency: "COP"'
        in normalized_body
    )

    assert (
        "Intl.NumberFormat"
        in normalized_body
    )

def test_admin_dashboard_pending_kpi_links_to_filtered_orders(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="admin-pending-order-count"'
        in body
    )

    assert (
        'href="/admin/orders?status=pending"'
        in body
    )

    assert (
        "Pedidos pendientes de gestión"
        in body
    )


def test_admin_dashboard_configures_auto_refresh(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
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
        "ADMIN_DATA_REFRESH_INTERVAL_MS"
        in normalized_body
    )

    assert (
        "30000"
        in normalized_body
    )

    assert (
        "function setupDashboardAutoRefresh("
        in normalized_body
    )

    assert (
        "window.setInterval("
        in normalized_body
    )

    assert (
        "refreshDashboardData"
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


def test_admin_dashboard_starts_auto_refresh_after_initial_load(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
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

    setup_index = (
        normalized_body.index(
            "function setupAdminDashboard()"
        )
    )

    initial_load_index = (
        normalized_body.index(
            "void loadDashboardSummary();",
            setup_index,
        )
    )

    auto_refresh_index = (
        normalized_body.index(
            "setupDashboardAutoRefresh();",
            setup_index,
        )
    )

    assert (
        initial_load_index <
        auto_refresh_index
    )


def test_admin_dashboard_includes_new_pending_orders_notice(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/admin/dashboard"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        'id="admin-dashboard-new-pending-notice"'
        in body
    )

    assert (
        'id="admin-dashboard-new-pending-notice-message"'
        in body
    )

    assert (
        'id="admin-dashboard-new-pending-notice-dismiss"'
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


def test_admin_dashboard_detects_increases_in_pending_orders(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/js/admin.js"
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
        "function observeDashboardPendingCount("
        in normalized_body
    )

    assert (
        "adminDashboardLastPendingCount === null"
        in normalized_body
    )

    assert (
        "adminDashboardUnseenNewPendingCount +=\n            increase"
        in normalized_body
    )

    assert (
        "function dismissDashboardNewPendingNotice("
        in normalized_body
    )

    assert (
        "setupDashboardNewPendingNotice();"
        in normalized_body
    )


def test_admin_css_preserves_hidden_attribute(
    monkeypatch,
):
    users = [
        AdminUserEntity(
            id=1,
            email="admin@test.com",
            password_hash="hash",
            is_active=True,
            token_version=0,
        )
    ]

    app, _ = _create_web_app(
        monkeypatch,
        users=users,
    )

    client = app.test_client()

    response = client.get(
        "/static/css/admin.css"
    )

    assert response.status_code == 200

    css = response.get_data(
        as_text=True
    )

    normalized_css = " ".join(
        css.split()
    )

    assert (
        "[hidden] { display: none !important; }"
        in normalized_css
    )