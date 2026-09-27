from app import create_app
from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)
from app.presentation.routes import auth_routes


class FakeAdminUserRepository:
    def __init__(
        self,
        admin_user,
    ):
        self.admin_user = admin_user

    def get_by_id(
        self,
        user_id,
    ):
        if (
            self.admin_user is not None
            and self.admin_user.id == user_id
        ):
            return self.admin_user

        return None


class FakeAuthService:
    def __init__(
        self,
    ):
        self.logout_calls = []

    def logout(
        self,
        user_id,
    ):
        self.logout_calls.append(
            user_id
        )

        return True


def test_logout_requires_authentication(
    monkeypatch,
):
    service = FakeAuthService()

    monkeypatch.setattr(
        auth_routes,
        "AuthService",
        lambda repository: service,
    )

    app = create_app(
        "development"
    )

    admin = AdminUserEntity(
        id=1,
        email="admin@loopandlove.com",
        password_hash="test-hash",
        is_active=True,
    )

    app.extensions[
        "admin_user_repository"
    ] = FakeAdminUserRepository(
        admin
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/logout"
    )

    assert response.status_code == 401

    assert (
        service.logout_calls
        == []
    )


def test_logout_revokes_authenticated_admin_session(
    monkeypatch,
):
    service = FakeAuthService()

    monkeypatch.setattr(
        auth_routes,
        "AuthService",
        lambda repository: service,
    )

    app = create_app(
        "development"
    )

    admin = AdminUserEntity(
        id=1,
        email="admin@loopandlove.com",
        password_hash="test-hash",
        is_active=True,
        token_version=0,
    )

    app.extensions[
        "admin_user_repository"
    ] = FakeAdminUserRepository(
        admin
    )

    token = (
        JWTService.create_access_token(
            user_id=1,
            email=admin.email,
            token_version=0,
        )
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/logout",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"] is None

    assert data["message"] == (
        "Sesión cerrada correctamente."
    )

    assert service.logout_calls == [
        1
    ]