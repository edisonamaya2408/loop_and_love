from io import BytesIO
from uuid import uuid4

import pytest
from PIL import Image

from app.domain.entities.admin_user import AdminUserEntity
from app.domain.entities.category import CategoryEntity
from app.domain.entities.product import ProductEntity
from app.infrastructure.database.models.admin_user_model import AdminUser
from app.infrastructure.database.models.category_model import Category
from app.infrastructure.database.models.product_model import Product
from app.infrastructure.database.repositories.admin_user_repository_impl import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.database.repositories.category_repository_impl import (
    SQLAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.product_repository_impl import (
    SQLAlchemyProductRepository,
)
from app.infrastructure.security.password_service import PasswordService
from app.infrastructure.storage.local_storage_repository import (
    LocalStorageRepository,
)


def _unique_suffix():
    return uuid4().hex[:10]


def _unique_email():
    return (
        f"integration-image-{_unique_suffix()}"
        "@loopandlove.test"
    )

def _image_bytes(
    image_format: str,
) -> bytes:
    """
    Genera una imagen real y mínima para pruebas
    de integración.

    Se utiliza para evitar enviar contenido ficticio
    a un endpoint que ahora valida los bytes reales.
    """

    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (10, 10),
        color=(255, 0, 0),
    )

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


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


@pytest.fixture
def persisted_category(
    app,
    integration_session,
):
    repository = SQLAlchemyCategoryRepository(
        session=integration_session,
    )

    suffix = _unique_suffix()

    created = repository.create(
        CategoryEntity(
            id=None,
            name=(
                f"Integration Image Category "
                f"{suffix}"
            ),
            slug=(
                f"integration-image-category-"
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
    app,
    integration_session,
    persisted_category,
):
    repository = SQLAlchemyProductRepository(
        session=integration_session,
    )

    suffix = _unique_suffix()

    created = repository.create(
        ProductEntity(
            id=None,
            code=(
                f"INTEGRATION-IMAGE-"
                f"{suffix.upper()}"
            ),
            name="Integration Image Product",
            description="Producto de imágenes.",
            price=15000,
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


def _auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.mark.integration
def test_admin_can_create_product_with_local_image(
    client,
    auth_token,
    persisted_category,
    integration_session,
):
    suffix = _unique_suffix()

    image_data = _image_bytes(
        "JPEG"
    )

    response = client.post(
        "/api/admin/products",
        data={
            "code": (
                f"INTEGRATION-IMAGE-"
                f"{suffix.upper()}"
            ),
            "name": "Producto con imagen",
            "description": "Imagen local.",
            "price": "25000",
            "category_id": str(
                persisted_category.id
            ),
            "is_active": "true",
            "image": (
                BytesIO(
                    image_data
                ),
                "producto.jpg",
            ),
        },
        headers=_auth_headers(auth_token),
        content_type="multipart/form-data",
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True

    product = data["data"]

    assert product["image_url"] is not None
    assert product["image_url"].startswith(
        "/static/uploads/products/"
    )
    assert product["image_url"].endswith(
        ".jpg"
    )

    product_id = product["id"]
    image_url = product["image_url"]

    storage = LocalStorageRepository()

    storage_path = storage._safe_destination(
        image_url.replace(
            "/static/uploads/",
            "",
        )
    )

    try:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            product_id,
        )

        assert persisted is not None
        assert persisted.image_url == image_url

        assert storage_path.exists()
        assert (
            storage_path.read_bytes()
            == image_data
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

        if storage_path.exists():
            storage_path.unlink()


@pytest.mark.integration
def test_admin_can_replace_product_image(
    client,
    auth_token,
    persisted_product,
    integration_session,
):
    original_image = (
        "products/"
        f"original-{_unique_suffix()}.jpg"
    )

    storage = LocalStorageRepository()

    storage.upload(
        file_data=b"original-image",
        file_path=original_image,
        content_type="image/jpeg",
    )

    original_image_url = (
        "/static/uploads/"
        + original_image
    )

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None

    persisted.image_url = original_image_url

    integration_session.commit()

    replacement_image_data = _image_bytes(
        "PNG"
    )

    response = client.put(
        f"/api/admin/products/"
        f"{persisted_product.id}",
        data={
            "code": persisted_product.code,
            "name": persisted_product.name,
            "description": persisted_product.description,
            "price": "16000",
            "category_id": str(
                persisted_product.category_id
            ),
            "is_active": "true",
            "image": (
                BytesIO(
                    replacement_image_data
                ),
                "reemplazo.png",
            ),
        },
        headers=_auth_headers(auth_token),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    new_image_url = data["data"]["image_url"]

    assert new_image_url.startswith(
        "/static/uploads/products/"
    )
    assert new_image_url.endswith(
        ".png"
    )
    assert new_image_url != original_image_url

    old_path = storage._safe_destination(
        original_image
    )

    new_path = storage._safe_destination(
        new_image_url.replace(
            "/static/uploads/",
            "",
        )
    )

    try:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            persisted_product.id,
        )

        assert persisted is not None
        assert persisted.image_url == new_image_url

        assert not old_path.exists()

        assert new_path.exists()

        assert (
            new_path.read_bytes()
            == replacement_image_data
        )

    finally:
        integration_session.expire_all()

        persisted = integration_session.get(
            Product,
            persisted_product.id,
        )

        if persisted is not None:
            persisted.image_url = None
            integration_session.commit()

        if old_path.exists():
            old_path.unlink()

        if new_path.exists():
            new_path.unlink()


@pytest.mark.integration
def test_admin_can_delete_product_with_image(
    client,
    auth_token,
    persisted_product,
    app,
    integration_session,
):
    image_path = (
        "products/"
        f"delete-{_unique_suffix()}.webp"
    )

    storage = LocalStorageRepository()

    storage.upload(
        file_data=b"delete-image",
        file_path=image_path,
        content_type="image/webp",
    )

    image_url = (
        "/static/uploads/"
        + image_path
    )

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None

    persisted.image_url = image_url

    integration_session.commit()

    response = client.delete(
        f"/api/admin/products/"
        f"{persisted_product.id}",
        headers=_auth_headers(auth_token),
    )

    assert response.status_code == 200

    integration_session.expire_all()

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is None

    physical_path = storage._safe_destination(
        image_path
    )

    assert not physical_path.exists()


@pytest.mark.integration
def test_admin_can_delete_product_image_without_deleting_product(
    client,
    auth_token,
    persisted_product,
    app,
    integration_session,
):
    image_path = (
        "products/"
        f"remove-{_unique_suffix()}.webp"
    )

    storage = LocalStorageRepository()

    storage.upload(
        file_data=b"image-to-remove",
        file_path=image_path,
        content_type="image/webp",
    )

    image_url = (
        "/static/uploads/"
        + image_path
    )

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None

    persisted.image_url = image_url

    integration_session.commit()

    physical_path = (
        storage._safe_destination(
            image_path
        )
    )

    assert physical_path.exists()

    response = client.delete(
        f"/api/admin/products/"
        f"{persisted_product.id}/image",
        headers=_auth_headers(
            auth_token
        ),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert (
        data["data"]["image_url"]
        is None
    )

    assert data["data"]["id"] == (
        persisted_product.id
    )

    assert data["message"] == (
        "Imagen del producto eliminada correctamente."
    )

    integration_session.expire_all()

    persisted = integration_session.get(
        Product,
        persisted_product.id,
    )

    assert persisted is not None

    assert (
        persisted.image_url
        is None
    )

    assert not physical_path.exists()