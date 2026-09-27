from uuid import uuid4

import pytest

from app.application.services.auth_service import AuthService
from app.domain.exceptions import (
    AuthenticationError,
)
from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.repositories.admin_user_repository_impl import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)


def _unique_email():
    return (
        f"integration-{uuid4().hex[:10]}"
        "@loopandlove.test"
    )


@pytest.fixture
def repository(
    integration_session,
):
    yield SQLAlchemyAdminUserRepository(
        session=integration_session
    )


@pytest.fixture
def persisted_admin(
    repository,
):
    email = _unique_email()

    admin_user = AdminUserEntity(
        id=None,
        email=email,
        password_hash=(
            PasswordService.hash_password(
                "Password123!"
            )
        ),
        is_active=True,
    )

    created = repository.create(
        admin_user
    )

    try:
        yield created

    finally:
        persisted = repository.session.get(
            AdminUser,
            created.id,
        )

        if persisted is not None:
            repository.session.delete(
                persisted
            )
            repository.session.commit()


@pytest.mark.integration
def test_admin_user_repository_get_by_email(
    repository,
    persisted_admin,
):
    result = repository.get_by_email(
        persisted_admin.email
    )

    assert result is not None
    assert result.id == persisted_admin.id
    assert result.email == persisted_admin.email
    assert result.is_active is True


@pytest.mark.integration
def test_admin_user_repository_get_by_id(
    repository,
    persisted_admin,
):
    result = repository.get_by_id(
        persisted_admin.id
    )

    assert result is not None
    assert result.id == persisted_admin.id
    assert result.email == persisted_admin.email
    assert (
        result.is_active
        is True
    )


@pytest.mark.integration
def test_admin_user_repository_returns_none_for_unknown_id(
    repository,
    persisted_admin,
):
    unknown_id = (
        persisted_admin.id + 1000000
    )

    result = repository.get_by_id(
        unknown_id
    )

    assert result is None


@pytest.mark.integration
def test_admin_user_repository_returns_none_for_unknown_email(
    repository,
):
    result = repository.get_by_email(
        _unique_email()
    )

    assert result is None


@pytest.mark.integration
def test_auth_service_logs_in_against_real_repository(
    repository,
    persisted_admin,
):
    service = AuthService(repository)

    token = service.login(
        email=(
            f"  {persisted_admin.email.upper()}  "
        ),
        password="Password123!",
    )

    assert isinstance(token, str)
    assert token


@pytest.mark.integration
def test_auth_service_rejects_wrong_password(
    repository,
    persisted_admin,
):
    service = AuthService(
        repository
    )

    with pytest.raises(
        AuthenticationError,
    ) as exc_info:
        service.login(
            email=persisted_admin.email,
            password="PasswordIncorrecta!",
        )

    assert str(
        exc_info.value
    ) == "Las credenciales no son válidas."


@pytest.mark.integration
def test_auth_service_rejects_inactive_admin(
    app,
    repository,
):
    with app.app_context():
        email = _unique_email()

        admin_user = AdminUserEntity(
            id=None,
            email=email,
            password_hash=(
                PasswordService.hash_password(
                    "Password123!"
                )
            ),
            is_active=False,
        )

        created = repository.create(
            admin_user
        )

        try:
            service = AuthService(
                repository
            )

            with pytest.raises(
                AuthenticationError,
            ) as exc_info:
                service.login(
                    email=email,
                    password="Password123!",
                )

            assert str(
                exc_info.value
            ) == "Las credenciales no son válidas."

        finally:
            persisted = repository.session.get(
                AdminUser,
                created.id,
            )

            if persisted is not None:
                repository.session.delete(
                    persisted
                )
                repository.session.commit()