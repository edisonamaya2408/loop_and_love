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
        f"integration-revocation-"
        f"{uuid4().hex[:10]}"
        "@loopandlove.test"
    )


@pytest.fixture
def persisted_admin(
    integration_session,
):
    repository = SQLAlchemyAdminUserRepository(
        session=integration_session,
    )

    created = repository.create(
        AdminUserEntity(
            id=None,
            email=_unique_email(),
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


def _login(
    client,
    email,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    return data["data"]["access_token"]


def _auth_headers(
    token,
):
    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }


@pytest.mark.integration
def test_logout_increments_admin_token_version(
    client,
    persisted_admin,
    integration_session,
):
    token = _login(
        client,
        persisted_admin.email,
    )

    response = client.post(
        "/api/auth/logout",
        headers=_auth_headers(
            token
        ),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    integration_session.expire_all()

    persisted = integration_session.get(
        AdminUser,
        persisted_admin.id,
    )

    assert persisted is not None

    assert (
        persisted.token_version
        == 1
    )


@pytest.mark.integration
def test_logout_invalidates_existing_token(
    client,
    persisted_admin,
):
    token = _login(
        client,
        persisted_admin.email,
    )

    before_logout = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            token
        ),
    )

    assert (
        before_logout.status_code
        == 200
    )

    logout_response = client.post(
        "/api/auth/logout",
        headers=_auth_headers(
            token
        ),
    )

    assert (
        logout_response.status_code
        == 200
    )

    after_logout = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            token
        ),
    )

    assert (
        after_logout.status_code
        == 401
    )

    data = after_logout.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )


@pytest.mark.integration
def test_new_login_receives_new_token_version_after_logout(
    client,
    persisted_admin,
):
    old_token = _login(
        client,
        persisted_admin.email,
    )

    logout_response = client.post(
        "/api/auth/logout",
        headers=_auth_headers(
            old_token
        ),
    )

    assert (
        logout_response.status_code
        == 200
    )

    new_token = _login(
        client,
        persisted_admin.email,
    )

    old_payload = jwt.decode(
        old_token,
        Config.JWT_SECRET_KEY,
        algorithms=["HS256"],
    )

    new_payload = jwt.decode(
        new_token,
        Config.JWT_SECRET_KEY,
        algorithms=["HS256"],
    )

    assert (
        old_payload["token_version"]
        == 0
    )

    assert (
        new_payload["token_version"]
        == 1
    )

    old_response = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            old_token
        ),
    )

    assert (
        old_response.status_code
        == 401
    )

    new_response = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            new_token
        ),
    )

    assert (
        new_response.status_code
        == 200
    )


@pytest.mark.integration
def test_logout_invalidates_all_previous_tokens_for_same_admin(
    client,
    persisted_admin,
):
    first_token = _login(
        client,
        persisted_admin.email,
    )

    second_token = _login(
        client,
        persisted_admin.email,
    )

    logout_response = client.post(
        "/api/auth/logout",
        headers=_auth_headers(
            first_token
        ),
    )

    assert (
        logout_response.status_code
        == 200
    )

    first_response = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            first_token
        ),
    )

    second_response = client.get(
        "/api/admin/categories",
        headers=_auth_headers(
            second_token
        ),
    )

    assert (
        first_response.status_code
        == 401
    )

    assert (
        second_response.status_code
        == 401
    )