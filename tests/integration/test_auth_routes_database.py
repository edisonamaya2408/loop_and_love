from uuid import uuid4

import jwt
import pytest

from app.config.settings import Config
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
        f"integration-route-{uuid4().hex[:10]}"
        "@loopandlove.test"
    )


@pytest.fixture
def persisted_admin(
    app,
    integration_session,
):
    repository = SQLAlchemyAdminUserRepository(
        session=integration_session,
    )

    email = _unique_email()

    created = repository.create(
        AdminUserEntity(
            id=None,
            email=email,
            password_hash=(
                PasswordService.hash_password(
                    "Password123!"
                )
            ),
            is_active=True,
        )
    )

    try:
        yield created

    finally:
        persisted = integration_session.get(
            AdminUser,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_login_endpoint_authenticates_real_admin(
    client,
    persisted_admin,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": (
                f"  {persisted_admin.email.upper()}  "
            ),
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["token_type"] == "Bearer"

    access_token = data["data"]["access_token"]

    assert isinstance(
        access_token,
        str,
    )

    assert access_token

    payload = jwt.decode(
        access_token,
        Config.JWT_SECRET_KEY,
        algorithms=["HS256"],
    )

    assert payload["sub"] == str(
        persisted_admin.id
    )

    assert payload["email"] == (
        persisted_admin.email
    )

    assert payload["type"] == "access"


@pytest.mark.integration
def test_login_endpoint_rejects_wrong_password(
    client,
    persisted_admin,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": persisted_admin.email,
            "password": "PasswordIncorrecta!",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data == {
        "success": False,
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": (
                "Las credenciales no son válidas."
            ),
        },
    }


@pytest.mark.integration
def test_login_endpoint_rejects_unknown_email(
    client,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": _unique_email(),
            "password": "Password123!",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data == {
        "success": False,
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": (
                "Las credenciales no son válidas."
            ),
        },
    }


@pytest.mark.integration
def test_login_endpoint_rejects_inactive_admin(
    app,
    client,
    integration_session,
):
    repository = SQLAlchemyAdminUserRepository(
        session=integration_session
    )

    email = _unique_email()

    created = repository.create(
        AdminUserEntity(
            id=None,
            email=email,
            password_hash=(
                PasswordService.hash_password(
                    "Password123!"
                )
            ),
            is_active=False,
        )
    )

    try:
        response = client.post(
            "/api/auth/login",
            json={
                "email": email,
                "password": "Password123!",
            },
        )

        assert response.status_code == 401

        data = response.get_json()

        assert data == {
            "success": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": (
                    "Las credenciales no son válidas."
                ),
            },
        }

    finally:
        persisted = integration_session.get(
            AdminUser,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_login_does_not_disclose_whether_admin_exists_or_is_active(
    client,
    persisted_admin,
    integration_session,
):
    existing_response = client.post(
        "/api/auth/login",
        json={
            "email": persisted_admin.email,
            "password": "WrongPassword123!",
        },
    )

    unknown_response = client.post(
        "/api/auth/login",
        json={
            "email": _unique_email(),
            "password": "WrongPassword123!",
        },
    )

    persisted = integration_session.get(
        AdminUser,
        persisted_admin.id,
    )

    assert persisted is not None

    persisted.is_active = False

    integration_session.commit()

    try:
        inactive_response = client.post(
            "/api/auth/login",
            json={
                "email": persisted_admin.email,
                "password": "Password123!",
            },
        )

        assert (
            existing_response.status_code
            == 401
        )

        assert (
            unknown_response.status_code
            == 401
        )

        assert (
            inactive_response.status_code
            == 401
        )

        assert (
            existing_response.get_json()
            == unknown_response.get_json()
            == inactive_response.get_json()
        )

    finally:
        persisted = integration_session.get(
            AdminUser,
            persisted_admin.id,
        )

        if persisted is not None:
            persisted.is_active = True
            integration_session.commit()