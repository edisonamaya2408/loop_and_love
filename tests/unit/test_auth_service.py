import pytest

from app.application.services.auth_service import AuthService
from app.domain.entities.admin_user import AdminUserEntity
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.security.jwt_service import (
    JWTService,
)
from app.domain.exceptions import (
    AuthenticationError,
)


class FakeAdminUserRepository:
    def __init__(self, user=None):
        self.user = user

    def get_by_email(self, email):
        if (
            self.user is not None
            and self.user.email == email
        ):
            return self.user

        return None

    def create(self, admin_user):
        self.user = admin_user
        return admin_user

    def increment_token_version(
        self,
        user_id,
    ):
        if (
            self.user is None
            or self.user.id != user_id
        ):
            return None

        self.user.token_version += 1

        return self.user


def _create_admin(
    email="admin@loopandlove.com",
    password="Password123!",
    is_active=True,
    token_version=0,
):
    return AdminUserEntity(
        id=1,
        email=email,
        password_hash=PasswordService.hash_password(
            password
        ),
        is_active=is_active,
        token_version=token_version,
    )


def test_login_returns_token_with_valid_credentials():
    admin = _create_admin()

    repository = FakeAdminUserRepository(admin)

    service = AuthService(repository)

    token = service.login(
        email="admin@loopandlove.com",
        password="Password123!",
    )

    assert isinstance(token, str)
    assert token


def test_login_normalizes_email():
    admin = _create_admin()

    repository = FakeAdminUserRepository(admin)

    service = AuthService(repository)

    token = service.login(
        email="  ADMIN@LOOPANDLOVE.COM  ",
        password="Password123!",
    )

    assert isinstance(token, str)


def test_login_rejects_invalid_password():
    admin = _create_admin()

    repository = FakeAdminUserRepository(
        admin
    )

    service = AuthService(
        repository
    )

    with pytest.raises(
        AuthenticationError,
    ):
        service.login(
            email="admin@loopandlove.com",
            password="incorrecta",
        )


def test_login_rejects_unknown_email():
    repository = FakeAdminUserRepository()

    service = AuthService(repository)

    with pytest.raises(
        AuthenticationError,
    ):
        service.login(
            email="noexiste@loopandlove.com",
            password="Password123!",
        )


def test_login_rejects_inactive_admin():
    admin = _create_admin(
        is_active=False
    )

    repository = FakeAdminUserRepository(
        admin
    )

    service = AuthService(
        repository
    )

    with pytest.raises(
        AuthenticationError,
    ):
        service.login(
            email="admin@loopandlove.com",
            password="Password123!",
        )

def test_login_embeds_current_token_version():
    admin = _create_admin(
        token_version=4
    )

    repository = FakeAdminUserRepository(
        admin
    )

    service = AuthService(
        repository
    )

    token = service.login(
        email=admin.email,
        password="Password123!",
    )

    payload = JWTService.decode_access_token(
        token
    )

    assert payload["token_version"] == 4


def test_logout_increments_token_version():
    admin = _create_admin(
        token_version=0
    )

    repository = FakeAdminUserRepository(
        admin
    )

    service = AuthService(
        repository
    )

    result = service.logout(
        admin.id
    )

    assert result is True
    assert (
        admin.token_version
        == 1
    )


def test_logout_returns_false_when_user_does_not_exist():
    repository = FakeAdminUserRepository()

    service = AuthService(
        repository
    )

    result = service.logout(
        1
    )

    assert result is False

def test_login_authentication_failures_use_same_error():
    service_unknown = AuthService(
        FakeAdminUserRepository()
    )

    inactive_admin = _create_admin(
        is_active=False
    )

    service_inactive = AuthService(
        FakeAdminUserRepository(
            inactive_admin
        )
    )

    service_wrong_password = AuthService(
        FakeAdminUserRepository(
            _create_admin()
        )
    )

    errors = []

    for service, email, password in [
        (
            service_unknown,
            "unknown@loopandlove.com",
            "Password123!",
        ),
        (
            service_inactive,
            "admin@loopandlove.com",
            "Password123!",
        ),
        (
            service_wrong_password,
            "admin@loopandlove.com",
            "wrong-password",
        ),
    ]:
        with pytest.raises(
            AuthenticationError
        ) as exc_info:
            service.login(
                email=email,
                password=password,
            )

        errors.append(
            str(exc_info.value)
        )

    assert errors == [
        "Las credenciales no son válidas.",
        "Las credenciales no son válidas.",
        "Las credenciales no son válidas.",
    ]