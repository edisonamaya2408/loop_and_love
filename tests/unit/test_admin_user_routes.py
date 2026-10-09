from app import create_app
from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)
from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)


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

    def get_by_email(
        self,
        email,
    ):
        for user in self.users:
            if user.email == email:
                return user

        return None

    def count(
        self,
    ):
        return len(
            self.users
        )

    def count_active(
        self,
    ):
        return sum(
            1
            for user in self.users
            if user.is_active
        )

    def list_all(
        self,
    ):
        return sorted(
            self.users,
            key=lambda user: user.email,
        )

    def create(
        self,
        admin_user,
    ):
        admin_user.id = (
            max(
                [
                    user.id
                    for user in self.users
                    if user.id is not None
                ],
                default=0,
            )
            + 1
        )

        self.users.append(
            admin_user
        )

        return admin_user

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

        existing.name = (
            admin_user.name
        )
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


def _create_test_app(
    users=None,
):
    app = create_app(
        "development"
    )

    app.extensions[
        "admin_audit_repository"
    ] = InMemoryAdminAuditRepository()

    repository = (
        FakeAdminUserRepository(
            users=users
        )
    )

    app.extensions[
        "admin_user_repository"
    ] = repository

    return app, repository


def _auth_headers(
    app,
    user,
):
    with app.app_context():
        token = (
            JWTService.create_access_token(
                user_id=user.id,
                email=user.email,
                token_version=user.token_version,
            )
        )

    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


def _admin():
    return AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )


def test_admin_users_requires_authentication():
    app, _ = _create_test_app(
        users=[_admin()]
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/users"
    )

    assert response.status_code == 401

    assert response.get_json()[
        "error"
    ][
        "code"
    ] == "AUTHENTICATION_REQUIRED"


def test_admin_users_lists_without_exposing_security_fields():
    admin = _admin()

    app, _ = _create_test_app(
        users=[admin]
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/users",
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["data"]) == 1

    returned_user = data[
        "data"
    ][0]

    assert returned_user[
        "name"
    ] == "Administrador"

    assert returned_user[
        "email"
    ] == "admin@test.com"

    assert "password_hash" not in (
        returned_user
    )

    assert "token_version" not in (
        returned_user
    )


def test_create_admin_user():
    admin = _admin()

    app, repository = _create_test_app(
        users=[admin]
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/users",
        json={
            "name": "Segundo administrador",
            "email": "  SECOND@Test.COM ",
            "password": "Password123!",
            "password_confirmation": "Password123!",
        },
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["name"] == "Segundo administrador"
    assert data["data"]["email"] == (
        "second@test.com"
    )
    assert data["data"]["is_active"] is True

    assert len(
        repository.users
    ) == 2


def test_create_admin_user_rejects_duplicate_email():
    admin = _admin()

    second = AdminUserEntity(
        id=2,
        email="second@test.com",
        password_hash="hash",
        is_active=True,
    )

    app, _ = _create_test_app(
        users=[
            admin,
            second,
        ]
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/users",
        json={
            "name": "Segundo administrador",
            "email": " SECOND@test.com ",
            "password": "Password123!",
            "password_confirmation": "Password123!",
        },
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 409

    assert response.get_json()[
        "error"
    ][
        "code"
    ] == "ADMIN_USER_EMAIL_ALREADY_EXISTS"


def test_update_admin_user_increments_token_version():
    admin = _admin()

    app, repository = _create_test_app(
        users=[admin]
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/users/1",
        json={
            "email": "updated@test.com",
        },
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["email"] == (
        "updated@test.com"
    )

    updated = repository.get_by_id(
        1
    )

    assert updated.token_version == 1


def test_update_admin_user_rejects_last_active_deactivation():
    admin = _admin()

    app, _ = _create_test_app(
        users=[admin]
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/users/1",
        json={
            "is_active": False,
        },
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 409

    data = response.get_json()

    assert data["error"][
        "code"
    ] == "ADMIN_USER_LAST_ACTIVE"


def test_update_admin_user_can_deactivate_one_of_two():
    admin = _admin()

    second = AdminUserEntity(
        id=2,
        email="second@test.com",
        password_hash="hash",
        is_active=True,
    )

    app, repository = _create_test_app(
        users=[
            admin,
            second,
        ]
    )

    client = app.test_client()

    response = client.patch(
        "/api/admin/users/2",
        json={
            "is_active": False,
        },
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 200

    assert repository.get_by_id(
        2
    ).is_active is False


def test_get_admin_user_returns_not_found():
    admin = _admin()

    app, _ = _create_test_app(
        users=[admin]
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/users/999",
        headers=_auth_headers(
            app,
            admin,
        ),
    )

    assert response.status_code == 404

    assert response.get_json()[
        "error"
    ][
        "code"
    ] == "ADMIN_USER_NOT_FOUND"