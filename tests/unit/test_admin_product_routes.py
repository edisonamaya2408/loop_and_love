from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace

import pytest

from app import create_app

from app.domain.exceptions import (
    DuplicateProductCodeError,
)
from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)


def _create_product(
    product_id=1,
    code="OSI-001",
    name="Amigurumi Oso",
    description="Oso tejido.",
    price=85000,
    category_id=1,
    image_url=None,
    is_active=True,
):
    return SimpleNamespace(
        id=product_id,
        code=code,
        name=name,
        description=description,
        price=Decimal(str(price)),
        category_id=category_id,
        image_url=image_url,
        is_active=is_active,
        created_at=None,
        updated_at=None,
    )


class FakeProductManagementService:
    def __init__(self):
        self.create_calls = []
        self.update_calls = []
        self.delete_calls = []
        self.remove_image_calls = []

        self.product = _create_product()

    def create_product(self, **kwargs):
        self.create_calls.append(kwargs)

        return _create_product(
            code=kwargs["code"],
            name=kwargs["name"],
            description=kwargs["description"],
         price=kwargs["price"],
            category_id=int(
                kwargs["category_id"]
            ),
            image_url=kwargs.get("image_url"),
            is_active=kwargs["is_active"],
        )

    def update_product(self, **kwargs):
        self.update_calls.append(kwargs)

        return _create_product(
            product_id=kwargs["product_id"],
            code=kwargs["code"],
            name=kwargs["name"],
            description=kwargs["description"],
            price=kwargs["price"],
            category_id=int(
                kwargs["category_id"]
            ),
            image_url=kwargs.get(
                "image_url",
                self.product.image_url,
            ),
            is_active=kwargs["is_active"],
        )

    def remove_product_image(
        self,
        product_id,
    ):
        self.remove_image_calls.append(
            product_id
        )

        if product_id != self.product.id:
            raise LookupError(
                "El producto no existe."
            )

        self.product.image_url = None

        return self.product

    def delete_product(
        self,
        product_id,
    ):
        self.delete_calls.append(
            product_id
        )

        if product_id != self.product.id:
            raise LookupError(
                "El producto no existe."
            )

        return self.product

    def to_response(
        self,
        product,
    ):
        return SimpleNamespace(
            id=product.id,
            code=product.code,
            name=product.name,
            description=product.description,
            price=product.price,
            category_id=product.category_id,
            category_name="Amigurumis",
            category_slug="amigurumis",
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )


class FakeProductService:
    def __init__(self):
        self.products = [
            _create_product()
        ]

    def get_product(
        self,
        product_id,
    ):
        if product_id == 1:
            return self.products[0]

        return None

    def list_all_products(self):
        return self.products

    def list_all_products_paginated(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
        is_active=None,
        page=None,
        per_page=None,
    ):
        page = int(page or 1)
        per_page = int(per_page or 12)

        products = self.products

        if is_active is not None:
            normalized = str(
                is_active
            ).lower()

            if normalized == "true":
                products = [
                    product
                    for product in products
                    if product.is_active
                ]

            elif normalized == "false":
                products = [
                    product
                    for product in products
                    if not product.is_active
                ]

        class Pagination:
            pass

        pagination = Pagination()
        pagination.page = page
        pagination.per_page = per_page
        pagination.total = len(products)
        pagination.pages = (
            (
                len(products)
                + per_page
                - 1
            )
            // per_page
            if products
            else 0
        )
        pagination.has_next = (
            page < pagination.pages
        )
        pagination.has_previous = (
            page > 1
        )

        class Result:
            pass

        result = Result()
        result.items = products[
            (page - 1) * per_page:
            page * per_page
        ]
        result.pagination = pagination

        return result

    def toggle_product_status(
        self,
        product_id,
        is_active,
    ):
        return _create_product(
            product_id=product_id,
            is_active=is_active,
        )

    def to_response(
        self,
        product,
    ):
        return SimpleNamespace(
            id=product.id,
            code=product.code,
            name=product.name,
            description=product.description,
            price=product.price,
            category_id=product.category_id,
            category_name="Amigurumis",
            category_slug="amigurumis",
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def to_responses(
        self,
        products,
    ):
        return [
            self.to_response(product)
            for product in products
        ]


def _create_test_app(
    monkeypatch,
):
    app = create_app("development")

    app.extensions[
        "admin_audit_repository"
    ] = InMemoryAdminAuditRepository()

    management_service = (
        FakeProductManagementService()
    )

    product_service = (
        FakeProductService()
    )

    monkeypatch.setattr(
        "app.presentation.routes.admin_product_routes."
        "_get_product_management_service",
        lambda: management_service,
    )

    monkeypatch.setattr(
        "app.presentation.routes.admin_product_routes."
        "_get_product_service",
        lambda: product_service,
    )

    return (
        app,
        management_service,
        product_service,
    )


def _auth_headers():
    """
    Genera un JWT válido utilizando el servicio real.
    """

    from app.infrastructure.security.jwt_service import (
        JWTService,
    )

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@test.com",
    )

    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_product_json(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        json={
            "code": "OSI-001",
            "name": "Amigurumi Oso",
            "description": "Oso tejido.",
            "price": "85000",
            "category_id": 1,
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["code"] == "OSI-001"
    assert data["data"]["image_url"] is None
    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    assert len(
        management_service.create_calls
    ) == 1

    call = (
        management_service.create_calls[0]
    )

    assert call["code"] == "OSI-001"
    assert call["name"] == "Amigurumi Oso"
    assert call["is_active"] is True
    assert call["image_data"] is None


def test_create_product_multipart_without_image(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-002",
            "name": "Amigurumi Gato",
            "description": "Gato tejido.",
            "price": "90000",
            "category_id": 1,
            "is_active": "true",
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["code"] == "OSI-002"

    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    call = (
        management_service.create_calls[0]
    )

    assert call["image_data"] is None
    assert call["image_filename"] is None
    assert call["image_content_type"] is None
    assert call["is_active"] is True


def test_create_product_multipart_with_image(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-003",
            "name": "Amigurumi Conejo",
            "description": "Conejo tejido.",
            "price": "95000",
            "category_id": 1,
            "is_active": "true",
            "image": (
                BytesIO(b"fake-jpeg-content"),
                "conejo.jpg",
            ),
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["code"] == "OSI-003"

    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    call = (
        management_service.create_calls[0]
    )

    assert call["image_data"] == (
        b"fake-jpeg-content"
    )

    assert call["image_filename"] == (
        "conejo.jpg"
    )

    assert call["image_content_type"] == (
        "image/jpeg"
    )


def test_create_product_multipart_converts_false_is_active(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-004",
            "name": "Amigurumi",
            "description": "Producto.",
            "price": "70000",
            "category_id": 1,
            "is_active": "false",
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    call = (
        management_service.create_calls[0]
    )

    assert call["is_active"] is False


def test_create_product_multipart_rejects_invalid_is_active(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-005",
            "name": "Amigurumi",
            "description": "Producto.",
            "price": "70000",
            "category_id": 1,
            "is_active": "not-a-boolean",
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["message"] == (
        "El campo is_active debe ser booleano."
    )


def test_update_product_multipart_without_image(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/products/1",
        data={
            "code": "OSI-001",
            "name": "Amigurumi Oso actualizado",
            "description": "Nueva descripción.",
            "price": "90000",
            "category_id": 1,
            "is_active": "true",
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["name"] == (
        "Amigurumi Oso actualizado"
    )

    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    call = (
        management_service.update_calls[0]
    )

    assert call["product_id"] == 1
    assert call["image_data"] is None


def test_update_product_multipart_with_new_image(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/products/1",
        data={
            "code": "OSI-001",
            "name": "Amigurumi Oso actualizado",
            "description": "Nueva descripción.",
            "price": "90000",
            "category_id": 1,
            "is_active": "true",
            "image": (
                BytesIO(b"new-jpeg-content"),
                "oso-nuevo.jpg",
            ),
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    call = (
        management_service.update_calls[0]
    )

    assert call["product_id"] == 1

    assert call["image_data"] == (
        b"new-jpeg-content"
    )

    assert call["image_filename"] == (
        "oso-nuevo.jpg"
    )

    assert call["image_content_type"] == (
        "image/jpeg"
    )


def test_update_product_requires_is_active(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/products/1",
        data={
            "code": "OSI-001",
            "name": "Amigurumi",
            "description": "Producto.",
            "price": "70000",
            "category_id": 1,
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["message"] == (
        "El campo is_active es obligatorio "
        "para actualizar el producto."
    )


def test_admin_products_requires_authentication(
    client,
):
    response = client.post(
        "/api/admin/products",
        json={
            "code": "OSI-001",
            "name": "Amigurumi",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_REQUIRED"
    )

def test_create_product_returns_409_when_code_already_exists(
    monkeypatch,
):
    app = create_app("development")

    def raise_duplicate_product_code():
        raise DuplicateProductCodeError(
            "OSI-001"
        )

    monkeypatch.setattr(
        "app.presentation.routes.admin_product_routes."
        "_get_product_management_service",
        raise_duplicate_product_code,
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        json={
            "code": "OSI-001",
            "name": "Amigurumi Oso",
            "description": "Oso tejido.",
            "price": "85000",
            "category_id": 1,
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 409

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "PRODUCT_CODE_ALREADY_EXISTS"
    )

    assert data["error"]["message"] == (
        "Ya existe un producto con el código OSI-001"
    )


def test_update_product_returns_409_when_code_already_exists(
    monkeypatch,
):
    app = create_app("development")

    def raise_duplicate_product_code():
        raise DuplicateProductCodeError(
            "OSI-002"
        )

    monkeypatch.setattr(
        "app.presentation.routes.admin_product_routes."
        "_get_product_management_service",
        raise_duplicate_product_code,
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/products/1",
        json={
            "code": "OSI-002",
            "name": "Amigurumi Oso actualizado",
            "description": "Nueva descripción.",
            "price": "90000",
            "category_id": 1,
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 409

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "PRODUCT_CODE_ALREADY_EXISTS"
    )

    assert data["error"]["message"] == (
        "Ya existe un producto con el código OSI-002"
    )

def test_admin_list_products_returns_paginated_response(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/products"
        "?page=1"
        "&per_page=12",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["data"]) == 1

    assert data["data"][0]["category_id"] == 1

    assert data["data"][0]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    assert data["pagination"] == {
        "page": 1,
        "per_page": 12,
        "total": 1,
        "pages": 1,
        "has_next": False,
        "has_previous": False,
    }


def test_admin_list_products_passes_filters(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/products"
        "?page=2"
        "&per_page=6"
        "&search=oso"
        "&category_id=1"
        "&min_price=50000"
        "&max_price=100000"
        "&is_active=true",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

def test_get_admin_product_returns_product(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/products/1",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == 1
    assert data["data"]["code"] == "OSI-001"
    assert data["data"]["name"] == (
        "Amigurumi Oso"
    )

    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

def test_get_admin_product_returns_404(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/products/999",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "PRODUCT_NOT_FOUND"
    )

def test_delete_admin_product(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/1",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == 1
    assert data["data"]["code"] == "OSI-001"
    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }
    assert data["message"] == (
        "Producto eliminado correctamente."
    )

    assert management_service.delete_calls == [
        1
    ]

def test_delete_admin_product_returns_404(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    def delete_product(product_id):
        management_service.delete_calls.append(
            product_id
        )

        raise LookupError(
            "El producto no existe."
        )

    management_service.delete_product = (
        delete_product
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/999",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "RESOURCE_NOT_FOUND"
    )

    assert management_service.delete_calls == [
        999
    ]

def test_delete_admin_product_requires_authentication(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/1"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert management_service.delete_calls == []

def test_delete_admin_product_image_returns_200(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    management_service.product.image_url = (
        "/static/uploads/products/oso.jpg"
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/1/image",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["id"] == 1

    assert data["data"]["image_url"] is None

    assert data["message"] == (
        "Imagen del producto eliminada correctamente."
    )

    assert (
        management_service.remove_image_calls
        == [1]
    )

def test_delete_admin_product_image_returns_404(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    def remove_product_image(
        product_id,
    ):
        management_service.remove_image_calls.append(
            product_id
        )

        raise LookupError(
            "El producto no existe."
        )

    management_service.remove_product_image = (
        remove_product_image
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/999/image",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "RESOURCE_NOT_FOUND"
    )

    assert (
        management_service.remove_image_calls
        == [999]
    )

def test_delete_admin_product_image_requires_authentication(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/1/image"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        management_service.remove_image_calls
        == []
    )

def test_delete_admin_product_image_returns_404_when_product_has_no_image(
    monkeypatch,
):
    (
        app,
        management_service,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    def remove_product_image(
        product_id,
    ):
        management_service.remove_image_calls.append(
            product_id
        )

        raise LookupError(
            "El producto no tiene una imagen."
        )

    management_service.remove_product_image = (
        remove_product_image
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/products/1/image",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False

    assert data["error"]["code"] == (
        "RESOURCE_NOT_FOUND"
    )

    assert data["error"]["message"] == (
        "El producto no tiene una imagen."
    )

def test_get_admin_product_requires_authentication(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/products/1"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

def test_create_product_rejects_request_above_http_limit(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    app.config[
        "MAX_CONTENT_LENGTH"
    ] = 1024

    client = app.test_client()

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-413",
            "name": "Producto demasiado grande",
            "description": "Prueba",
            "price": "90000",
            "category_id": "1",
            "is_active": "true",
            "image": (
                BytesIO(b"x" * 4096),
                "producto.jpg",
            ),
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 413

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "REQUEST_ENTITY_TOO_LARGE"
    )

def test_create_product_rejects_image_above_file_limit(
    monkeypatch,
):
    (
        app,
        _,
        _,
    ) = _create_test_app(
        monkeypatch
    )

    app.config[
        "MAX_CONTENT_LENGTH"
    ] = 2 * 1024 * 1024

    app.config[
        "MAX_IMAGE_SIZE_MB"
    ] = 1

    client = app.test_client()

    oversized_image = (
        b"x"
        * (
            1 * 1024 * 1024
            + 1
        )
    )

    response = client.post(
        "/api/admin/products",
        data={
            "code": "OSI-IMAGE-413",
            "name": "Imagen demasiado grande",
            "description": "Prueba",
            "price": "90000",
            "category_id": "1",
            "is_active": "true",
            "image": (
                BytesIO(
                    oversized_image
                ),
                "producto.jpg",
            ),
        },
        headers=_auth_headers(),
        content_type="multipart/form-data",
    )

    assert response.status_code == 413

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "REQUEST_ENTITY_TOO_LARGE"
    )