from uuid import uuid4

import pytest

from app.domain.entities.admin_user import AdminUserEntity
from app.domain.entities.category import CategoryEntity
from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.repositories.admin_user_repository_impl import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)


def _unique_email():
    return (
        f"integration-admin-{uuid4().hex[:10]}"
        "@loopandlove.test"
    )


def _unique_category():
    suffix = uuid4().hex[:10]

    return CategoryEntity(
        id=None,
        name=f"Integration Admin Category {suffix}",
        slug=f"integration-admin-category-{suffix}",
        is_active=True,
    )


@pytest.fixture
def persisted_admin(
    app,
    integration_session,
):
    repository = SQLAlchemyAdminUserRepository(
        session=integration_session,
    )

    created = repository.create(
        AdminUserEntity(
            id=None,
            email=_unique_email(),
            password_hash=PasswordService.hash_password(
                "Password123!"
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


@pytest.fixture
def persisted_category(
    app,
    integration_session,
):
    repository = SQLAlchemyCategoryRepository(
        session=integration_session,
    )

    created = repository.create(
        _unique_category()
    )

    try:
        yield created

    finally:
        persisted = integration_session.get(
            Category,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


def _login(client, email):
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


@pytest.mark.integration
def test_authenticated_admin_can_list_categories(
    client,
    persisted_admin,
    persisted_category,
):
    token = _login(
        client,
        persisted_admin.email,
    )

    response = client.get(
        "/api/admin/categories",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert isinstance(data["data"], list)

    category_ids = {
        category["id"]
        for category in data["data"]
    }

    assert persisted_category.id in category_ids


@pytest.mark.integration
def test_authenticated_admin_can_get_category(
    client,
    persisted_admin,
    persisted_category,
):
    token = _login(
        client,
        persisted_admin.email,
    )

    response = client.get(
        f"/api/admin/categories/{persisted_category.id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["id"] == (
        persisted_category.id
    )

    assert data["data"]["name"] == (
        persisted_category.name
    )

    assert data["data"]["slug"] == (
        persisted_category.slug
    )

    assert data["data"]["is_active"] is True


@pytest.mark.integration
def test_admin_category_endpoint_requires_authentication(
    client,
):
    response = client.get(
        "/api/admin/categories",
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_REQUIRED"
    )


@pytest.mark.integration
def test_admin_category_endpoint_rejects_invalid_token(
    client,
):
    response = client.get(
        "/api/admin/categories",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )


@pytest.mark.integration
def test_deactivated_admin_cannot_use_existing_token(
    client,
    persisted_admin,
    integration_session,
):
    token = _login(
        client,
        persisted_admin.email,
    )

    persisted = integration_session.get(
        AdminUser,
        persisted_admin.id,
    )

    assert persisted is not None

    persisted.is_active = False

    integration_session.commit()

    try:
        response = client.get(
            "/api/admin/categories",
            headers={
                "Authorization": (
                    f"Bearer {token}"
                ),
            },
        )

        assert response.status_code == 401

        data = response.get_json()

        assert data["success"] is False

        assert (
            data["error"]["code"]
            == "INVALID_OR_EXPIRED_TOKEN"
        )

    finally:
        persisted = integration_session.get(
            AdminUser,
            persisted_admin.id,
        )

        if persisted is not None:
            persisted.is_active = True
            integration_session.commit()