from decimal import Decimal
from types import SimpleNamespace

import pytest

from app import create_app
from app.domain.entities.product import ProductEntity
from app.presentation.routes import product_routes


class FakeProductService:
    def __init__(
        self,
        products=None,
    ):
        self.products = products or []
        self.list_calls = []
        self.active_product_calls = []

    def list_active_products_paginated(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
        page=None,
        per_page=None,
    ):
        self.list_calls.append(
            {
                "search": search,
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price,
                "page": page,
                "per_page": per_page,
            }
        )

        page = int(page or 1)
        per_page = int(per_page or 12)

        class Pagination:
            pass

        pagination = Pagination()
        pagination.page = page
        pagination.per_page = per_page
        pagination.total = len(self.products)

        pagination.pages = (
            (
                len(self.products)
                + per_page
                - 1
            )
            // per_page
            if self.products
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
        result.items = self.products
        result.pagination = pagination

        return result

    def get_active_product(
        self,
        product_id,
    ):
        self.active_product_calls.append(
            product_id
        )

        for product in self.products:
            if product.id == product_id:
                return product

        return None

    def _category_response(
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

    def to_response(
        self,
        product,
    ):
        return self._category_response(
            product
        )

    def to_responses(
        self,
        products,
    ):
        return [
            self._category_response(product)
            for product in products
        ]


def _create_product(
    product_id=1,
    is_active=True,
):
    return ProductEntity(
        id=product_id,
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price=Decimal("85000"),
        category_id=1,
        image_url="https://example.com/oso.jpg",
        is_active=is_active,
        created_at=None,
        updated_at=None,
    )


@pytest.fixture
def app(monkeypatch):
    app = create_app("development")

    service = FakeProductService(
        products=[
            _create_product()
        ]
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    return app


def test_list_products_returns_paginated_response(
    app,
):
    client = app.test_client()

    response = client.get(
        "/api/products"
        "?page=2"
        "&per_page=6"
        "&search=oso"
        "&category_id=1"
        "&min_price=50000"
        "&max_price=100000"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert len(data["data"]) == 1

    assert data["data"][0]["id"] == 1
    assert data["data"][0]["code"] == "OSI-001"
    assert data["data"][0]["category_id"] == 1

    assert data["data"][0]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    assert data["pagination"] == {
        "page": 2,
        "per_page": 6,
        "total": 1,
        "pages": 1,
        "has_next": False,
        "has_previous": True,
    }

    assert data["data"][0]["price"] == (
        "85000.00"
    )


def test_list_products_passes_query_parameters_to_service(
    app,
    monkeypatch,
):
    service = FakeProductService(
        products=[
            _create_product()
        ]
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    client = app.test_client()

    response = client.get(
        "/api/products"
        "?page=2"
        "&per_page=6"
        "&search=oso"
        "&category_id=1"
        "&min_price=50000"
        "&max_price=100000"
    )

    assert response.status_code == 200

    assert service.list_calls == [
        {
            "search": "oso",
            "category_id": "1",
            "min_price": "50000",
            "max_price": "100000",
            "page": "2",
            "per_page": "6",
        }
    ]


def test_get_product_returns_active_product(
    app,
):
    client = app.test_client()

    response = client.get(
        "/api/products/1"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["data"]["id"] == 1
    assert data["data"]["is_active"] is True
    assert data["data"]["category_id"] == 1

    assert data["data"]["category"] == {
        "id": 1,
        "name": "Amigurumis",
        "slug": "amigurumis",
    }

    assert data["data"]["price"] == (
        "85000.00"
    )


def test_get_product_returns_404_when_not_found(
    app,
    monkeypatch,
):
    service = FakeProductService(
        products=[]
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    client = app.test_client()

    response = client.get(
        "/api/products/999"
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "PRODUCT_NOT_FOUND"
    )


def test_get_product_does_not_expose_inactive_product(
    app,
    monkeypatch,
):
    service = FakeProductService(
        products=[]
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    client = app.test_client()

    response = client.get(
        "/api/products/1"
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["success"] is False
    assert data["error"]["code"] == (
        "PRODUCT_NOT_FOUND"
    )

class CategoryValidationProductService:
    def __init__(
        self,
        error_message,
    ):
        self.error_message = error_message

    def list_active_products_paginated(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
        page=None,
        per_page=None,
    ):
        raise LookupError(
            self.error_message
        )

def test_list_products_returns_404_for_nonexistent_category(
    app,
    monkeypatch,
):
    service = CategoryValidationProductService(
        "La categoría no existe."
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    client = app.test_client()

    response = client.get(
        "/api/products?category_id=999999"
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "RESOURCE_NOT_FOUND"
    )
    assert (
        payload["error"]["message"]
        == "La categoría no existe."
    )

def test_list_products_returns_404_for_inactive_category(
    app,
    monkeypatch,
):
    service = CategoryValidationProductService(
        "La categoría no existe."
    )

    monkeypatch.setattr(
        product_routes,
        "ProductService",
        lambda *args, **kwargs: service,
    )

    client = app.test_client()

    response = client.get(
        "/api/products?category_id=2"
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "RESOURCE_NOT_FOUND"
    )

def test_product_route_serializes_price_without_float_conversion(
    app,
):
    client = app.test_client()

    response = client.get(
        "/api/products/1"
    )

    assert response.status_code == 200

    data = response.get_json()

    price = data["data"]["price"]

    assert isinstance(
        price,
        str,
    )

    assert price == "85000.00"