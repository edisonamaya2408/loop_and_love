from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.application.services.product_service import (
    ProductService,
)


class FakeProductRepository:
    pass


class FakeCategoryRepository:
    def __init__(self):

        self.get_by_id_calls = []
        self.get_by_ids_calls = []

        self.categories = {
            1: SimpleNamespace(
                id=1,
                name="Amigurumis",
                slug="amigurumis",
                is_active=True,
            )
        }

    def get_by_id(
        self,
        category_id,
    ):
        self.get_by_id_calls.append(
            category_id
        )

        return self.categories.get(
            category_id
        )

    def get_by_ids(
        self,
        category_ids,
    ):
        self.get_by_ids_calls.append(
            set(category_ids)
        )

        return {
            category_id: self.categories[
                category_id
            ]
            for category_id in category_ids
            if category_id in self.categories
        }


def test_to_response_includes_category_data():
    service = ProductService(
        repository=FakeProductRepository(),
        category_repository=FakeCategoryRepository(),
    )

    now = datetime.now(timezone.utc)

    product = SimpleNamespace(
        id=1,
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price=Decimal("85000"),
        category_id=1,
        image_url=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    response = service.to_response(
        product
    )

    assert response.id == 1
    assert response.code == "OSI-001"
    assert response.category_id == 1
    assert response.category_name == "Amigurumis"
    assert response.category_slug == "amigurumis"


def test_to_response_handles_missing_category():
    service = ProductService(
        repository=FakeProductRepository(),
        category_repository=FakeCategoryRepository(),
    )

    product = SimpleNamespace(
        id=1,
        code="OSI-001",
        name="Amigurumi Oso",
        description=None,
        price=Decimal("85000"),
        category_id=999,
        image_url=None,
        is_active=True,
        created_at=None,
        updated_at=None,
    )

    response = service.to_response(
        product
    )

    assert response.category_id == 999
    assert response.category_name is None
    assert response.category_slug is None

def test_to_responses_converts_multiple_products():
    service = ProductService(
        repository=FakeProductRepository(),
        category_repository=FakeCategoryRepository(),
    )

    products = [
        SimpleNamespace(
            id=1,
            code="OSI-001",
            name="Amigurumi Oso",
            description="Oso tejido.",
            price=Decimal("85000"),
            category_id=1,
            image_url=None,
            is_active=True,
            created_at=None,
            updated_at=None,
        ),
        SimpleNamespace(
            id=2,
            code="GAT-001",
            name="Amigurumi Gato",
            description="Gato tejido.",
            price=Decimal("90000"),
            category_id=1,
            image_url=None,
            is_active=True,
            created_at=None,
            updated_at=None,
        ),
    ]

    responses = service.to_responses(
        products
    )

    assert len(responses) == 2
    assert responses[0].category_name == (
        "Amigurumis"
    )
    assert responses[1].category_slug == (
        "amigurumis"
    )

    assert (
        len(
            service.category_repository
            .get_by_ids_calls
        )
        == 1
    )

    assert (
        service.category_repository
        .get_by_ids_calls[0]
        == {1}
    )

    assert (
        service.category_repository
        .get_by_id_calls
        == []
    )

def test_to_responses_fetches_each_category_only_once():
    category_repository = (
        FakeCategoryRepository()
    )

    category_repository.categories[2] = (
        SimpleNamespace(
            id=2,
            name="Decoración",
            slug="decoracion",
            is_active=True,
        )
    )

    service = ProductService(
        repository=FakeProductRepository(),
        category_repository=category_repository,
    )

    products = [
        SimpleNamespace(
            id=1,
            code="OSI-001",
            name="Amigurumi Oso",
            description="Oso tejido.",
            price=Decimal("85000"),
            category_id=1,
            image_url=None,
            is_active=True,
            created_at=None,
            updated_at=None,
        ),
        SimpleNamespace(
            id=2,
            code="DEC-001",
            name="Decoración Corazón",
            description="Decoración tejida.",
            price=Decimal("45000"),
            category_id=2,
            image_url=None,
            is_active=True,
            created_at=None,
            updated_at=None,
        ),
        SimpleNamespace(
            id=3,
            code="OSI-002",
            name="Amigurumi Oso pequeño",
            description="Oso tejido.",
            price=Decimal("65000"),
            category_id=1,
            image_url=None,
            is_active=True,
            created_at=None,
            updated_at=None,
        ),
    ]

    responses = service.to_responses(
        products
    )

    assert len(responses) == 3

    assert responses[0].category_name == (
        "Amigurumis"
    )

    assert responses[1].category_name == (
        "Decoración"
    )

    assert responses[2].category_name == (
        "Amigurumis"
    )

    assert (
        category_repository.get_by_ids_calls
        == [{1, 2}]
    )

    assert (
        category_repository.get_by_id_calls
        == []
    )