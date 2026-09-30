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