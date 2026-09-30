import pytest

from app.application.services.admin_setup_service import (
    AdminSetupService,
)
from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.exceptions import (
    AdminSetupNotRequiredError,
    AdminSetupUnavailableError,
    InvalidAdminSetupTokenError,
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


def _service(
    repository=None,
    token="A" * 40,
):
    return AdminSetupService(
        repository=(
            repository
            or FakeAdminUserRepository()
        ),
        setup_token=token,
    )


def test_setup_is_required_when_no_admin_exists():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    assert (
        service.setup_required()
        is True
    )


def test_setup_is_not_required_when_an_admin_exists():
    repository = (
        FakeAdminUserRepository(
            users=[
                AdminUserEntity(
                    id=1,
                    email="admin@test.com",
                    password_hash="hash",
                    is_active=True,
                )
            ]
        )
    )

    service = _service(
        repository
    )

    assert (
        service.setup_required()
        is False
    )


def test_create_initial_admin_successfully():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    created = service.create_initial_admin(
        setup_token="A" * 40,
        email="Admin@Example.COM",
        password="Password123!",
        password_confirmation="Password123!",
    )

    assert created.id == 1
    assert created.email == "admin@example.com"
    assert created.is_active is True
    assert created.token_version == 0
    assert created.password_hash != "Password123!"
    assert repository.count() == 1


def test_create_initial_admin_rejects_invalid_setup_token():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    with pytest.raises(
        InvalidAdminSetupTokenError
    ):
        service.create_initial_admin(
            setup_token="incorrect-token",
            email="admin@test.com",
            password="Password123!",
            password_confirmation="Password123!",
        )

    assert repository.count() == 0


def test_create_initial_admin_requires_valid_setup_configuration():
    repository = (
        FakeAdminUserRepository()
    )

    service = AdminSetupService(
        repository=repository,
        setup_token="short",
    )

    with pytest.raises(
        AdminSetupUnavailableError
    ):
        service.create_initial_admin(
            setup_token="short",
            email="admin@test.com",
            password="Password123!",
            password_confirmation="Password123!",
        )

    assert repository.count() == 0


def test_create_initial_admin_rejects_when_setup_already_completed():
    repository = (
        FakeAdminUserRepository(
            users=[
                AdminUserEntity(
                    id=1,
                    email="existing@test.com",
                    password_hash="hash",
                    is_active=True,
                )
            ]
        )
    )

    service = _service(
        repository
    )

    with pytest.raises(
        AdminSetupNotRequiredError
    ):
        service.create_initial_admin(
            setup_token="A" * 40,
            email="new@test.com",
            password="Password123!",
            password_confirmation="Password123!",
        )

    assert repository.count() == 1


def test_create_initial_admin_rejects_invalid_email():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    with pytest.raises(
        ValueError,
        match="correo electrónico no es válido",
    ):
        service.create_initial_admin(
            setup_token="A" * 40,
            email="correo-invalido",
            password="Password123!",
            password_confirmation="Password123!",
        )

    assert repository.count() == 0


def test_create_initial_admin_rejects_short_password():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    with pytest.raises(
        ValueError,
        match="al menos 8 caracteres",
    ):
        service.create_initial_admin(
            setup_token="A" * 40,
            email="admin@test.com",
            password="123",
            password_confirmation="123",
        )

    assert repository.count() == 0


def test_create_initial_admin_rejects_password_mismatch():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    with pytest.raises(
        ValueError,
        match="contraseñas no coinciden",
    ):
        service.create_initial_admin(
            setup_token="A" * 40,
            email="admin@test.com",
            password="Password123!",
            password_confirmation="Different123!",
        )

    assert repository.count() == 0