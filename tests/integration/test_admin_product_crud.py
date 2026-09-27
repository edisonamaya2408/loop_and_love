from decimal import Decimal
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


def _unique_suffix():
    return uuid4().hex[:10]


def _unique_email():
    return (
        f"integration-product-{_unique_suffix()}"
        "@loopandlove.test"
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

    assert data["success"] is True

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

    suffix = _unique_suffix()

    created = repository.create(
        CategoryEntity(
            id=None,
            name=(
                "Integration Product Category "
                f"{suffix}"
            ),
            slug=(
                "integration-product-category-"
                f"{suffix}"
            ),
            is_active=True,
        )
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


@pytest.fixture
def persisted_product(
    integration_session,
    persisted_category,
):
    repository = SQLAlchemyProductRepository(
        session=integration_session
    )

    code = (
        "INTEGRATION-PRODUCT-"
        f"{_unique_suffix().upper()}"
    )

    created = repository.create(
        ProductEntity(
            id=None,
            code=code,
            name="Integration Product",
            description="Producto de integración.",
            price=Decimal("15000.00"),
            category_id=persisted_category.id,
            image_url=None,
            is_active=True,
        )
    )

    try:
        yield created

    finally:
        persisted = integration_session.get(
            Product,
            created.id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_admin_can_create_product_without_image(
    client,
    auth_token,
    persisted_category,
    integration_session,
):
    suffix = _unique_suffix()

    code = (
        "INTEGRATION-CREATE-"
        f"{suffix.upper()}"
    )

    name = f"Producto creado {suffix}"

    response = client.post(
        "/api/admin/products",
        json={
            "code": code,
            "name": name,
            "description": (
                "Producto creado desde integración."
            ),
            "price": "25000.50",
            "category_id": (
                persisted_category.id
            ),
            "is_active": True,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True

    product = data["data"]

    assert product["code"] == code
    assert product["name"] == name
    assert product["price"] == (
        "25000.50"
    )
    assert product["category_id"] == (
        persisted_category.id
    )
    assert product["category"] == {
        "id": persisted_category.id,
        "name": persisted_category.name,
        "slug": persisted_category.slug,
    }
    assert product["image_url"] is None
    assert product["is_active"] is True

    product_id = product["id"]

    try:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            product_id,
        )

        assert persisted is not None
        assert persisted.code == code
        assert persisted.category_id == (
            persisted_category.id
        )

    finally:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            product_id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()


@pytest.mark.integration
def test_admin_can_get_product(
    client,
    auth_token,
    persisted_product,
):
    response = client.get(
        f"/api/admin/products/"
        f"{persisted_product.id}",
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == (
        persisted_product.id
    )
    assert data["data"]["code"] == (
        persisted_product.code
    )
    assert data["data"]["category_id"] == (
        persisted_product.category_id
    )
    assert data["data"]["category"] is not None


@pytest.mark.integration
def test_admin_can_update_product(
    client,
    auth_token,
    persisted_product,
    integration_session,
):
    response = client.put(
        f"/api/admin/products/"
        f"{persisted_product.id}",
        json={
            "code": persisted_product.code,
            "name": (
                "Producto actualizado "
                "Integration"
            ),
            "description": (
                "Descripción actualizada."
            ),
            "price": "32000.75",
            "category_id": (
                persisted_product.category_id
            ),
            "is_active": False,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    product = data["data"]

    assert product["id"] == (
        persisted_product.id
    )
    assert product["name"] == (
        "Producto actualizado Integration"
    )
    assert product["price"] == (
        "32000.75"
    )
    assert product["category_id"] == (
        persisted_product.category_id
    )
    assert product["is_active"] is False

    integration_session.expire_all()

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None
    assert persisted.name == (
        "Producto actualizado Integration"
    )
    assert persisted.price == Decimal(
        "32000.75"
    )
    assert persisted.is_active is False


@pytest.mark.integration
def test_admin_can_toggle_product_status(
    client,
    auth_token,
    persisted_product,
    integration_session,
):
    response = client.patch(
        f"/api/admin/products/"
        f"{persisted_product.id}/status",
        json={
            "is_active": False,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == (
        persisted_product.id
    )
    assert data["data"]["is_active"] is False

    integration_session.expire_all()

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None
    assert persisted.is_active is False


@pytest.mark.integration
def test_admin_can_delete_product(
    client,
    auth_token,
    persisted_product,
    integration_session,
):
    product_id = persisted_product.id

    response = client.delete(
        f"/api/admin/products/{product_id}",
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == product_id
    assert data["message"] == (
        "Producto eliminado correctamente."
    )

    integration_session.expire_all()

    persisted = integration_session.get(
        Product,
        product_id,
    )

    assert persisted is None


@pytest.mark.integration
def test_admin_cannot_create_product_with_duplicate_code(
    client,
    auth_token,
    persisted_product,
    persisted_category,
):
    response = client.post(
        "/api/admin/products",
        json={
            "code": persisted_product.code,
            "name": "Producto duplicado",
            "description": "Debe fallar.",
            "price": "20000",
            "category_id": (
                persisted_category.id
            ),
            "is_active": True,
        },
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 409

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "PRODUCT_CODE_ALREADY_EXISTS"
    )
    assert (
        "código"
        in data["error"]["message"].lower()
    )


@pytest.mark.integration
def test_admin_cannot_create_product_with_inactive_category(
    app,
    client,
    auth_token,
    integration_session,
):
    category_repository = (
        SQLAlchemyCategoryRepository(
            session=integration_session
        )
    )

    suffix = _unique_suffix()

    inactive_category = (
        category_repository.create(
            CategoryEntity(
                id=None,
                name=(
                    "Integration Inactive "
                    f"Category {suffix}"
                ),
                slug=(
                    "integration-inactive-"
                    f"category-{suffix}"
                ),
                is_active=False,
            )
        )
    )

    category_id = inactive_category.id

    try:
        response = client.post(
            "/api/admin/products",
            json={
                "code": (
                    "INTEGRATION-INACTIVE-"
                    f"{_unique_suffix().upper()}"
                ),
                "name": (
                    "Producto categoría inactiva"
                ),
                "description": "Debe fallar.",
                "price": "15000",
                "category_id": category_id,
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
        assert (
            "inactiva"
            in data["error"]["message"].lower()
        )

    finally:
        integration_session.expire_all()

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
def test_admin_product_price_preserves_decimal_precision(
    client,
    auth_token,
    persisted_category,
    integration_session,
):
    suffix = _unique_suffix()

    response = client.post(
        "/api/admin/products",
        json={
            "code": (
                "INTEGRATION-DECIMAL-"
                f"{suffix.upper()}"
            ),
            "name": "Producto decimal exacto",
            "description": (
                "Prueba de precisión monetaria."
            ),
            "price": "12500.50",
            "category_id": (
                persisted_category.id
            ),
            "is_active": True,
        },
        headers=_auth_headers(
            auth_token
        ),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["price"] == (
        "12500.50"
    )

    product_id = data["data"]["id"]

    try:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            product_id,
        )

        assert persisted is not None

        assert persisted.price == (
            Decimal("12500.50")
        )

        assert isinstance(
            persisted.price,
            Decimal,
        )

    finally:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            product_id,
        )

        if persisted is not None:
            integration_session.delete(
                persisted
            )
            integration_session.commit()

@pytest.mark.integration
def test_admin_rejects_price_with_more_than_two_decimals(
    client,
    auth_token,
    persisted_category,
):
    suffix = _unique_suffix()

    response = client.post(
        "/api/admin/products",
        json={
            "code": (
                "INTEGRATION-BAD-DECIMAL-"
                f"{suffix.upper()}"
            ),
            "name": "Producto inválido",
            "description": "Debe ser rechazado.",
            "price": "12500.505",
            "category_id": (
                persisted_category.id
            ),
            "is_active": True,
        },
        headers=_auth_headers(
            auth_token
        ),
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "VALIDATION_ERROR"
    )

    assert (
        "máximo 2 decimales"
        in data["error"]["message"]
    )