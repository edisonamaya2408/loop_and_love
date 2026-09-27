from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.services.product_service import ProductService
from app.domain.exceptions import (
    DuplicateProductCodeError,
)

class FakeProductRepository:
    def __init__(self):
        self.products = {}
        self.next_id = 1
        self.active_calls = []

    def get_by_id(self, product_id):
        return self.products.get(product_id)

    def get_by_code(self, code):
        for product in self.products.values():
            if product.code == code:
                return product

        return None

    def get_active(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
    ):
        self.active_calls.append(
            {
                "search": search,
                "category_id": category_id,
                "min_price": min_price,
                "max_price": max_price,
            }
        )

        products = [
            product
            for product in self.products.values()
            if product.is_active
        ]

        if search:
            search = search.lower()

            products = [
                product
                for product in products
                if search in product.name.lower()
                or (
                    product.description
                    and search in product.description.lower()
                )
            ]

        if category_id is not None:
            products = [
                product
                for product in products
                if product.category_id == category_id
            ]

        if min_price is not None:
            products = [
                product
                for product in products
                if product.price >= min_price
            ]

        if max_price is not None:
            products = [
                product
                for product in products
                if product.price <= max_price
            ]

        return products

    def get_active_by_id(self, product_id):
        product = self.products.get(product_id)

        if product is None:
            return None

        if not product.is_active:
            return None

        return product

    def get_active_paginated(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
        offset=0,
        limit=12,
    ):
        products = self.get_active(
            search=search,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
        )

        total = len(products)

        return (
            products[offset:offset + limit],
            total,
        )

    def get_all(self):
        return list(self.products.values())

    def create(self, product):
        product.id = self.next_id

        self.products[product.id] = product

        self.next_id += 1

        return product

    def update(self, product):
        self.products[product.id] = product

        return product

    def delete(
        self,
        product_id,
    ):
        return self.products.pop(
            product_id,
            None,
        )

    def get_all_paginated(
        self,
        search=None,
        category_id=None,
        min_price=None,
        max_price=None,
        is_active=None,
        offset=0,
        limit=12,
    ):

        self.last_category_id = category_id
        
        products = list(
            self.products.values()
        )

        if is_active is not None:
            products = [
                product
                for product in products
                if product.is_active == is_active
            ]

        if search:
            search = search.lower()

            products = [
                product
                for product in products
                if search in product.name.lower()
                or search in product.code.lower()
                or (
                    product.description
                    and search
                    in product.description.lower()
                )
            ]

        if category_id is not None:
            products = [
                product
                for product in products
                if product.category_id == category_id
            ]

        if min_price is not None:
            products = [
                product
                for product in products
                if product.price >= min_price
            ]

        if max_price is not None:
            products = [
                product
                for product in products
                if product.price <= max_price
            ]

        total = len(products)

        return (
            products[offset:offset + limit],
            total,
        )

class FakeCategoryRepository:
    def __init__(self):
        self.last_category_id = None
        self.categories = {
            1: SimpleNamespace(
                id=1,
                name="Amigurumis",
                slug="amigurumis",
                is_active=True,
            ),
            2: SimpleNamespace(
                id=2,
                name="Decoración",
                slug="decoracion",
                is_active=False,
            ),
        }

    def get_by_id(self, category_id):
        return self.categories.get(category_id)

    def get_by_ids(
        self,
        category_ids,
    ):
        return {
            category_id: self.categories[
                category_id
            ]
            for category_id in category_ids
            if category_id in self.categories
        }

def _create_service():
    repository = FakeProductRepository()
    category_repository = FakeCategoryRepository()

    return (
        ProductService(
            repository=repository,
            category_repository=category_repository,
        ),
        repository,
    )


def _create_product(service):
    return service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido a mano.",
        price="85000",
        category_id=1,
        image_url="https://example.com/oso.jpg",
        is_active=True,
    )


def test_list_active_products_cleans_filters():
    service, repository = _create_service()

    result = service.list_active_products(
        search="  oso  ",
        category_id="1",
        min_price="30000",
        max_price="100000",
    )

    assert result == []

    assert repository.active_calls == [
        {
            "search": "oso",
            "category_id": 1,
            "min_price": Decimal("30000"),
            "max_price": Decimal("100000"),
        }
    ]


def test_create_product():
    service, repository = _create_service()

    product = _create_product(service)

    assert product.id == 1
    assert product.code == "OSI-001"
    assert product.name == "Amigurumi Oso"
    assert product.price == Decimal("85000")
    assert product.is_active is True

    assert repository.get_by_id(1) is product


def test_create_product_rejects_string_boolean():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="El campo is_active debe ser booleano.",
    ):
        service.create_product(
            code="OSI-001",
            name="Amigurumi Oso",
            description=None,
            price="85000",
            category_id=1,
            image_url=None,
            is_active="true",
        )


def test_update_product():
    service, _ = _create_service()

    product = _create_product(service)

    updated = service.update_product(
        product_id=product.id,
        code="OSI-001",
        name="Oso Crochet",
        description="Nueva descripción",
        price="95000",
        category_id=1,
        image_url="https://example.com/nuevo.jpg",
        is_active=True,
    )

    assert updated.code == "OSI-001"
    assert updated.name == "Oso Crochet"
    assert updated.price == Decimal("95000")
    assert updated.description == "Nueva descripción"


def test_remove_product_image():
    service, repository = _create_service()

    product = _create_product(
        service
    )

    product.image_url = (
        "https://example.com/oso.jpg"
    )

    updated, old_image_url = (
        service.remove_product_image(
            product.id
        )
    )

    assert updated.image_url is None

    assert old_image_url == (
        "https://example.com/oso.jpg"
    )

    assert repository.get_by_id(
        product.id
    ).image_url is None


def test_remove_product_image_raises_when_product_does_not_exist():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="El producto no existe.",
    ):
        service.remove_product_image(
            999
        )


def test_remove_product_image_raises_when_product_has_no_image():
    service, repository = _create_service()

    product = _create_product(
        service
    )

    product.image_url = None

    repository.update(
        product
    )

    with pytest.raises(
        LookupError,
        match="El producto no tiene una imagen.",
    ):
        service.remove_product_image(
            product.id
        )
        

def test_toggle_product_status():
    service, _ = _create_service()

    product = _create_product(service)

    updated = service.toggle_product_status(
        product_id=product.id,
        is_active=False,
    )

    assert updated.is_active is False


def test_update_nonexistent_product():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="El producto no existe.",
    ):
        service.update_product(
            product_id=999,
            code="PROD-999",
            name="Producto",
            description=None,
            price="50000",
            category_id=1,
            image_url=None,
            is_active=True,
        )


def test_list_active_products_rejects_invalid_price():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="El precio debe ser un número válido.",
    ):
        service.list_active_products(
            min_price="abc"
        )


def test_list_active_products_rejects_negative_price():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="El precio no puede ser negativo.",
    ):
        service.list_active_products(
            min_price="-100"
        )

def test_create_product_normalizes_price_to_two_decimals():
    service, _ = _create_service()

    product = service.create_product(
        code="DEC-001",
        name="Producto decimal",
        description=None,
        price="12500.50",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    assert product.price == Decimal(
        "12500.50"
    )


def test_create_product_rejects_more_than_two_decimals():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="máximo 2 decimales",
    ):
        service.create_product(
            code="DEC-002",
            name="Producto decimal",
            description=None,
            price="12500.505",
            category_id=1,
            image_url=None,
            is_active=True,
        )


def test_create_product_rejects_price_above_database_precision():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="máximo permitido",
    ):
        service.create_product(
            code="DEC-003",
            name="Producto fuera de rango",
            description=None,
            price="10000000000.00",
            category_id=1,
            image_url=None,
            is_active=True,
        )


def test_create_product_rejects_float_price():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="debe ser un número válido",
    ):
        service.create_product(
            code="DEC-004",
            name="Producto float",
            description=None,
            price=12500.50,
            category_id=1,
            image_url=None,
            is_active=True,
        )


def test_list_active_products_rejects_more_than_two_decimal_filter():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="máximo 2 decimales",
    ):
        service.list_active_products(
            min_price="100.001"
        )


def test_list_active_products_rejects_invalid_range():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match=(
            "El precio mínimo no puede ser mayor "
            "al precio máximo."
        ),
    ):
        service.list_active_products(
            min_price="100000",
            max_price="30000",
        )


def test_get_product_rejects_invalid_id():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="El ID del producto debe ser mayor que cero.",
    ):
        service.get_product(0)


def test_create_product_rejects_duplicate_code():
    service, _ = _create_service()

    _create_product(service)

    with pytest.raises(
        DuplicateProductCodeError,
        match="Ya existe un producto con el código OSI-001",
    ):
        service.create_product(
            code="OSI-001",
            name="Otro producto",
            description="Otra descripción.",
            price="90000",
            category_id=1,
            image_url=None,
            is_active=True,
        )


def test_create_product_accepts_different_codes():
    service, _ = _create_service()

    first = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido a mano.",
        price="85000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    second = service.create_product(
        code="OSI-002",
        name="Amigurumi Oso Grande",
        description="Oso tejido a mano grande.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    assert first.code == "OSI-001"
    assert second.code == "OSI-002"
    assert first.id != second.id


def test_update_product_rejects_duplicate_code():
    service, _ = _create_service()

    first = _create_product(service)

    second = service.create_product(
        code="OSI-002",
        name="Otro producto",
        description="Otra descripción.",
        price="90000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    with pytest.raises(
        DuplicateProductCodeError,
        match="Ya existe un producto con el código OSI-001",
    ):
        service.update_product(
            product_id=second.id,
            code=first.code,
            name="Producto actualizado",
            description="Descripción actualizada.",
            price="100000",
            category_id=1,
            image_url=None,
            is_active=True,
        )

def test_list_active_products_paginated():
    service, repository = _create_service()

    first = _create_product(service)

    second = service.create_product(
        code="OSI-002",
        name="Amigurumi Conejo",
        description="Conejo tejido a mano.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    result = service.list_active_products_paginated(
        page=1,
        per_page=1,
    )

    assert result.items == [first]
    assert result.pagination.page == 1
    assert result.pagination.per_page == 1
    assert result.pagination.total == 2
    assert result.pagination.pages == 2
    assert result.pagination.has_next is True
    assert result.pagination.has_previous is False

    assert repository.active_calls[-1] == {
        "search": None,
        "category_id": None,
        "min_price": None,
        "max_price": None,
    }


def test_list_active_products_paginated_second_page():
    service, _ = _create_service()

    _create_product(service)

    second = service.create_product(
        code="OSI-002",
        name="Amigurumi Conejo",
        description="Conejo tejido a mano.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    result = service.list_active_products_paginated(
        page=2,
        per_page=1,
    )

    assert result.items == [second]
    assert result.pagination.page == 2
    assert result.pagination.total == 2
    assert result.pagination.pages == 2
    assert result.pagination.has_next is False
    assert result.pagination.has_previous is True


def test_list_active_products_paginated_validates_pagination():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="page debe ser mayor que cero",
    ):
        service.list_active_products_paginated(
            page=0
        )

    with pytest.raises(
        ValueError,
        match="per_page no puede ser mayor que 50",
    ):
        service.list_active_products_paginated(
            per_page=51
        )


def test_get_active_product_does_not_return_inactive_product():
    service, _ = _create_service()

    product = _create_product(service)

    service.toggle_product_status(
        product.id,
        False,
    )

    result = service.get_active_product(
        product.id
    )

    assert result is None


def test_get_active_product_returns_active_product():
    service, _ = _create_service()

    product = _create_product(service)

    result = service.get_active_product(
        product.id
    )

    assert result is product

def test_list_all_products_paginated_returns_all_statuses():
    service, _ = _create_service()

    active = _create_product(service)

    inactive = service.create_product(
        code="OSI-002",
        name="Amigurumi Conejo",
        description="Conejo tejido.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=False,
    )

    result = service.list_all_products_paginated(
        page=1,
        per_page=12,
    )

    assert result.items == [
        active,
        inactive,
    ]

    assert result.pagination.total == 2
    assert result.pagination.pages == 1


def test_list_all_products_paginated_filters_active():
    service, _ = _create_service()

    active = _create_product(service)

    service.create_product(
        code="OSI-002",
        name="Amigurumi Conejo",
        description="Conejo tejido.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=False,
    )

    result = service.list_all_products_paginated(
        is_active="true",
    )

    assert result.items == [active]
    assert result.pagination.total == 1


def test_list_all_products_paginated_filters_inactive():
    service, _ = _create_service()

    service.create_product(
        code="OSI-002",
        name="Amigurumi Conejo",
        description="Conejo tejido.",
        price="95000",
        category_id=1,
        image_url=None,
        is_active=False,
    )

    result = service.list_all_products_paginated(
        is_active="false",
    )

    assert len(result.items) == 1
    assert result.items[0].code == "OSI-002"
    assert result.items[0].is_active is False


def test_list_all_products_paginated_rejects_invalid_status():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="is_active debe ser booleano",
    ):
        service.list_all_products_paginated(
            is_active="invalid",
        )


def test_list_all_products_paginated_filters_code():
    service, _ = _create_service()

    product = _create_product(service)

    result = service.list_all_products_paginated(
        search="OSI-001",
    )

    assert result.items == [product]
    assert result.pagination.total == 1

def test_list_active_products_paginated_rejects_page_above_maximum():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="page no puede ser mayor que 10000",
    ):
        service.list_active_products_paginated(
            page=10001,
            per_page=50,
        )


def test_list_all_products_paginated_rejects_page_above_maximum():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="page no puede ser mayor que 10000",
    ):
        service.list_all_products_paginated(
            page=10001,
            per_page=50,
        )


def test_delete_product_removes_existing_product():
    service, repository = _create_service()

    product = _create_product(service)

    deleted = service.delete_product(
        product.id
    )

    assert deleted is product
    assert product.id not in repository.products


def test_delete_product_raises_when_product_does_not_exist():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="El producto no existe",
    ):
        service.delete_product(999)

def test_list_active_products_rejects_nonexistent_category():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="La categoría no existe",
    ):
        service.list_active_products_paginated(
            category_id="999999"
        )

def test_list_active_products_rejects_inactive_category():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="La categoría no existe",
    ):
        service.list_active_products_paginated(
            category_id="2"
        )

def test_list_all_products_accepts_inactive_category():
    service, repository = _create_service()

    service.list_all_products_paginated(
        category_id="2"
    )

    assert (
        repository.last_category_id
        == 2
    )

def test_create_product_normalizes_code():
    service, repository = _create_service()

    product = service.create_product(
        code="  oso-001 ",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="90000",
        category_id=1,
        image_url=None,
        is_active=True,
    )

    assert product.code == "OSO-001"

def test_create_product_rejects_code_with_different_case():
    service, _ = _create_service()

    _create_product(
        service
    )

    with pytest.raises(
        DuplicateProductCodeError
    ):
        service.create_product(
            code=" osi-001 ",
            name="Otro producto",
            description="Otro producto.",
            price="90000",
            category_id=1,
            image_url=None,
            is_active=True,
        )