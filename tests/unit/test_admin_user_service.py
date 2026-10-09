import pytest

from app.application.services.admin_user_service import (
    AdminUserService,
)
from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.exceptions import (
    AdminUserLastActiveError,
    DuplicateAdminUserEmailError,
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


def _service(
    repository,
):
    return AdminUserService(
        repository
    )


def test_create_user_normalizes_email_and_hashes_password(
    monkeypatch,
):
    repository = (
        FakeAdminUserRepository()
    )

    monkeypatch.setattr(
        "app.application.services.admin_user_service.PasswordService.hash_password",
        lambda password: f"hashed::{password}",
    )

    service = _service(
        repository
    )

    created = (
        service.create_user(
            name="Administrador de prueba",
            email="  ADMIN@Test.COM ",
            password="Password123!",
            password_confirmation="Password123!",
        )
    )

    assert created.id == 1
    assert created.name == "Administrador de prueba"
    assert created.email == (
        "admin@test.com"
    )
    assert created.password_hash == (
        "hashed::Password123!"
    )
    assert created.is_active is True
    assert created.token_version == 0


def test_create_user_rejects_duplicate_email():
    existing = AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
    )

    repository = (
        FakeAdminUserRepository(
            users=[existing]
        )
    )

    service = _service(
        repository
    )

    with pytest.raises(
        DuplicateAdminUserEmailError
    ):
        service.create_user(
            name="Administrador de prueba",
            email="ADMIN@test.com",
            password="Password123!",
            password_confirmation="Password123!",
        )


def test_create_user_rejects_short_password():
    repository = (
        FakeAdminUserRepository()
    )

    service = _service(
        repository
    )

    with pytest.raises(
        ValueError,
        match="al menos 8",
    ):
        service.create_user(
            name="Administrador de prueba",
            email="admin@test.com",
            password="123",
            password_confirmation="123",
        )


def test_update_user_changes_email_and_invalidates_tokens(
    monkeypatch,
):
    user = AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )

    repository = (
        FakeAdminUserRepository(
            users=[user]
        )
    )

    service = _service(
        repository
    )

    updated = (
        service.update_user(
            user_id=1,
            changes={
                "email": "NewAdmin@Test.COM",
            },
        )
    )

    assert updated.email == (
        "newadmin@test.com"
    )

    assert updated.token_version == 1


def test_update_user_changes_password_and_invalidates_tokens(
    monkeypatch,
):
    user = AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="old-hash",
        is_active=True,
        token_version=0,
    )

    repository = (
        FakeAdminUserRepository(
            users=[user]
        )
    )

    monkeypatch.setattr(
        "app.application.services.admin_user_service.PasswordService.hash_password",
        lambda password: f"hashed::{password}",
    )

    service = _service(
        repository
    )

    updated = (
        service.update_user(
            user_id=1,
            changes={
                "password": "Password456!",
                "password_confirmation": "Password456!",
            },
        )
    )

    assert updated.password_hash == (
        "hashed::Password456!"
    )

    assert updated.token_version == 1


def test_update_user_can_deactivate_admin_when_another_active_admin_exists():
    users = [
        AdminUserEntity(
            id=1,
            email="one@test.com",
            password_hash="hash",
            is_active=True,
        ),
        AdminUserEntity(
            id=2,
            email="two@test.com",
            password_hash="hash",
            is_active=True,
        ),
    ]

    repository = (
        FakeAdminUserRepository(
            users=users
        )
    )

    service = _service(
        repository
    )

    updated = (
        service.update_user(
            user_id=2,
            changes={
                "is_active": False,
            },
        )
    )

    assert updated.is_active is False
    assert updated.token_version == 1


def test_update_user_rejects_deactivating_last_active_admin():
    user = AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
    )

    repository = (
        FakeAdminUserRepository(
            users=[user]
        )
    )

    service = _service(
        repository
    )

    with pytest.raises(
        AdminUserLastActiveError
    ):
        service.update_user(
            user_id=1,
            changes={
                "is_active": False,
            },
        )

    assert user.is_active is True


def test_update_user_rejects_duplicate_email():
    users = [
        AdminUserEntity(
            id=1,
            email="one@test.com",
            password_hash="hash",
            is_active=True,
        ),
        AdminUserEntity(
            id=2,
            email="two@test.com",
            password_hash="hash",
            is_active=True,
        ),
    ]

    repository = (
        FakeAdminUserRepository(
            users=users
        )
    )

    service = _service(
        repository
    )

    with pytest.raises(
        DuplicateAdminUserEmailError
    ):
        service.update_user(
            user_id=1,
            changes={
                "email": "two@test.com",
            },
        )


def test_update_user_rejects_without_effective_changes():
    user = AdminUserEntity(
        id=1,
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )

    repository = (
        FakeAdminUserRepository(
            users=[user]
        )
    )

    service = _service(
        repository
    )

    with pytest.raises(
        ValueError,
        match="No hay cambios",
    ):
        service.update_user(
            user_id=1,
            changes={
                "email": "ADMIN@test.com",
                "is_active": True,
            },
        )


def test_create_user_rejects_empty_name():
    service = _service(FakeAdminUserRepository())

    with pytest.raises(
        ValueError,
        match="nombre del administrador es obligatorio",
    ):
        service.create_user(
            name="   ",
            email="admin@test.com",
            password="Password123!",
            password_confirmation="Password123!",
        )


def test_update_user_changes_name_and_invalidates_tokens():
    user = AdminUserEntity(
        id=1,
        name="Nombre anterior",
        email="admin@test.com",
        password_hash="hash",
        is_active=True,
        token_version=0,
    )

    repository = FakeAdminUserRepository(users=[user])
    service = _service(repository)

    updated = service.update_user(
        user_id=1,
        changes={"name": "  María   Pérez  "},
    )

    assert updated.name == "María Pérez"
    assert updated.token_version == 1
