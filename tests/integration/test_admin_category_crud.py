from uuid import uuid4

import pytest

from app.domain.entities.admin_user import AdminUserEntity
from app.domain.entities.category import CategoryEntity
from app.domain.entities.product import ProductEntity
from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.repositories.admin_user_repository_impl import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)


def _unique_email():
    return (
        f"integration-category-crud-{uuid4().hex[:10]}"
        "@loopandlove.test"
    )


def _unique_category():
    suffix = uuid4().hex[:10]

    return CategoryEntity(
        id=None,
        name=f"Integration CRUD {suffix}",
        slug=f"integration-crud-{suffix}",
        is_active=True,
    )


@pytest.fixture
def persisted_admin(
    integration_session,
):
    repository = SQLAlchemyAdminUserRepository(
        session=integration_session
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
def auth_token(
    client,
    persisted_admin,
):
    response = client.post(
        "/api/auth/login",
        json={
            "email": persisted_admin.email,
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    return data["data"]["access_token"]


def _auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def persisted_category(
    integration_session,
):
    repository = SQLAlchemyCategoryRepository(
        session=integration_session
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


@pytest.mark.integration
def test_admin_can_create_category(
    client,
    auth_token,
    integration_session,
):
    suffix = uuid4().hex[:10]
    category_name = (
        f"Integration Created {suffix}"
    )
    category_slug = (
        f"integration-created-{suffix}"
    )

    response = client.post(
        "/api/admin/categories",
        json={
            "name": category_name,
            "is_active": True,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["name"] == category_name
    assert data["data"]["slug"] == category_slug
    assert data["data"]["is_active"] is True

    category_id = data["data"]["id"]

    try:
        persisted = integration_session.get(
            Category,
            category_id,
        )

        assert persisted is not None
        assert persisted.name == category_name
        assert persisted.slug == category_slug

    finally:
        persisted = integration_session.get(
            Category,
            category_id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_admin_can_update_category(
    client,
    auth_token,
    persisted_category,
    integration_session,
):
    response = client.put(
        f"/api/admin/categories/"
        f"{persisted_category.id}",
        json={
            "name": "Integration Category Updated",
            "is_active": False,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == (
        persisted_category.id
    )
    assert data["data"]["name"] == (
        "Integration Category Updated"
    )
    assert data["data"]["slug"] == (
        "integration-category-updated"
    )
    assert data["data"]["is_active"] is False

    persisted = integration_session.get(
        Category,
        persisted_category.id,
    )

    assert persisted is not None
    assert persisted.name == (
        "Integration Category Updated"
    )
    assert persisted.slug == (
        "integration-category-updated"
    )
    assert persisted.is_active is False


@pytest.mark.integration
def test_admin_can_delete_category_without_products(
    client,
    auth_token,
    persisted_category,
    integration_session,
):
    category_id = persisted_category.id

    response = client.delete(
        f"/api/admin/categories/{category_id}",
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == category_id

    persisted = integration_session.get(
        Category,
        category_id,
    )

    assert persisted is None


@pytest.mark.integration
def test_admin_cannot_delete_category_with_products(
    client,
    auth_token,
    app,
    integration_session,
):
    category_repository = (
        SQLAlchemyCategoryRepository(
            session=integration_session
        )
    )

    product_category = category_repository.create(
        _unique_category()
    )

    product = ProductEntity(
        id=None,
        code=(
            f"INTEGRATION-CRUD-"
            f"{uuid4().hex[:10].upper()}"
        ),
        name="Integration Category Product",
        description="Producto de prueba.",
        price=10000,
        category_id=product_category.id,
        image_url=None,
        is_active=True,
    )

    product_repository = SQLAlchemyProductRepository(
        session=integration_session
    )

    created_product = product_repository.create(
        product
    )

    category_id = product_category.id
    product_id = created_product.id

    try:
        response = client.delete(
            f"/api/admin/categories/{category_id}",
            headers=_auth_headers(auth_token),
        )

        assert response.status_code == 400

        data = response.get_json()

        assert data["success"] is False
        assert data["error"]["code"] == (
            "VALIDATION_ERROR"
        )
        assert (
            "tiene productos asociados"
            in data["error"]["message"]
        )

        persisted_category = (
            integration_session.get(
                Category,
                category_id,
            )
        )

        persisted_product = (
            integration_session.get(
                Product,
                product_id,
            )
        )

        assert persisted_category is not None
        assert persisted_product is not None

    finally:
        persisted_product = integration_session.get(
            Product,
            product_id,
        )

        persisted_category = integration_session.get(
            Category,
            category_id,
        )

        if persisted_product is not None:
            integration_session.delete(
                persisted_product
            )

        if persisted_category is not None:
            integration_session.delete(
                persisted_category
            )

        integration_session.commit()


@pytest.mark.integration
def test_admin_cannot_create_duplicate_category_name(
    client,
    auth_token,
    persisted_category,
):
    response = client.post(
        "/api/admin/categories",
        json={
            "name": persisted_category.name,
            "is_active": True,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "VALIDATION_ERROR"
    )
    assert "Ya existe una categoría" in (
        data["error"]["message"]
    )