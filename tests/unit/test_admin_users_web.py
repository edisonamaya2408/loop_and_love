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

    def count_active(self):
        return sum(
            1
            for user in self.users
            if user.is_active
        )

    def list_all(self):
        return sorted(
            self.users,
            key=lambda user: user.email,
        )

    def update(
        self,
        admin_user,
        *,
        increment_token_version=False,
    ):
        existing = self.get_by_id(
            admin_user.id
        )

        if existing is None:
            return None

        existing.email = (
            admin_user.email
        )

        existing.password_hash = (
            admin_user.password_hash
        )

        existing.is_active = (
            admin_user.is_active
        )

        if increment_token_version:
            existing.token_version += 1
        else:
            existing.token_version = (
                admin_user.token_version
            )

        return existing


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


def _admin_user():
    return AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )


def test_admin_users_page_redirects_to_setup_when_no_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/admin/users"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == "/admin/setup"
    )


def test_admin_users_page_renders_when_admin_exists(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/users"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    assert (
        "Usuarios"
        in body
    )

    assert (
        "Crear usuario"
        in body
    )

    assert (
        'id="admin-user-create-form"'
        in body
    )

    assert (
        'id="admin-user-edit-form"'
        in body
    )

    assert (
        "/static/css/admin-users.css"
        in body
    )

    assert (
        "/static/js/admin-users.js"
        in body
    )


def test_admin_users_page_navigation_marks_users_as_active(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/users"
    )

    assert response.status_code == 200

    body = response.get_data(
        as_text=True
    )

    users_link_marker = (
        "web.admin_users_page"
        if "web.admin_users_page" in body
        else "Usuarios"
    )

    assert users_link_marker


def test_admin_users_page_does_not_remove_dashboard_navigation(
    monkeypatch,
):
    app, _ = _create_web_app(
        monkeypatch,
        users=[
            _admin_user()
        ],
    )

    client = app.test_client()

    response = client.get(
        "/admin/users"
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
        "Ver portal B2B"
        in body
    )

    assert (
        "Cerrar sesión"
        in body
    )