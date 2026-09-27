from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.application.services.product_management_service import (
    ProductManagementService,
)
from app.application.services.product_service import (
    ProductService,
)
from app.domain.entities.product import ProductEntity
from app.domain.exceptions import (
    DuplicateProductCodeError,
)


class FakeProductRepository:
    def __init__(self):
        self.products = {}
        self.next_id = 1
        self.fail_update = False

    def get_by_id(
        self,
        product_id,
    ):
        return self.products.get(
            product_id
        )

    def get_by_code(
        self,
        code,
    ):
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
        return []

    def get_all(self):
        return list(
            self.products.values()
        )

    def create(
        self,
        product,
    ):
        product.id = self.next_id

        self.products[
            product.id
        ] = product

        self.next_id += 1

        return product

    def update(
        self,
        product,
    ):
        if self.fail_update:
            raise RuntimeError(
                "Database unavailable"
            )

        self.products[
            product.id
        ] = product

        return product

    def delete(
        self,
        product_id,
    ):
        return self.products.pop(
            product_id,
            None,
        )


class FakeCategoryRepository:
    def __init__(self):
        self.categories = {
            1: SimpleNamespace(
                id=1,
                name="Amigurumis",
                slug="amigurumis",
                is_active=True,
            ),
        }

    def get_by_id(self, category_id):
        return self.categories.get(category_id)


class FakeImageStorageService:
    def __init__(self):
        self.uploads = []
        self.deleted = []
        self.fail_upload = False
        self.fail_delete = False
        self.next_upload_id = 1

    def upload_product_image(
        self,
        file_data,
        filename,
        content_type,
    ):
        if self.fail_upload:
            raise RuntimeError(
                "Storage unavailable"
            )

        url = (
            "https://example.com/products/"
            f"{self.next_upload_id}.jpg"
        )

        self.next_upload_id += 1

        self.uploads.append(
            {
                "file_data": file_data,
                "filename": filename,
                "content_type": content_type,
                "url": url,
            }
        )

        return url

    def delete_product_image(
        self,
        image_url,
    ):
        if self.fail_delete:
            raise RuntimeError(
                "Storage delete failed"
            )

        self.deleted.append(
            image_url
        )


def _create_service():
    repository = FakeProductRepository()

    category_repository = FakeCategoryRepository()

    product_service = ProductService(
        repository=repository,
        category_repository=category_repository,
    )

    image_storage_service = (
        FakeImageStorageService()
    )

    management_service = (
        ProductManagementService(
            product_service=product_service,
            image_storage_service=image_storage_service,
        )
    )

    return (
        management_service,
        repository,
        image_storage_service,
    )


def test_create_product_without_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        is_active=True,
    )

    assert product.id == 1
    assert product.image_url is None

    assert storage.uploads == []

    assert len(
        repository.products
    ) == 1


def test_create_product_with_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"fake-image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    assert product.image_url == (
        "https://example.com/products/1.jpg"
    )

    assert len(
        storage.uploads
    ) == 1

    assert (
        storage.uploads[0]["file_data"]
        == b"fake-image"
    )

    assert len(
        repository.products
    ) == 1


def test_create_product_deletes_uploaded_image_when_product_creation_fails():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    existing_product = ProductEntity(
        id=None,
        code="OSI-001",
        name="Producto existente",
        description=None,
        price=Decimal("50000"),
        category_id=1,
        image_url=None,
        is_active=True,
    )

    repository.create(
        existing_product
    )

    with pytest.raises(
        DuplicateProductCodeError,
        match="Ya existe un producto con el código OSI-001",
    ):
        service.create_product(
            code="OSI-001",
            name="Otro producto",
            description=None,
            price="85000",
            category_id=1,
            image_data=b"fake-image",
            image_filename="oso.jpg",
            image_content_type="image/jpeg",
            is_active=True,
        )

    assert len(
        storage.uploads
    ) == 1

    assert storage.deleted == [
        "https://example.com/products/1.jpg"
    ]

    assert len(
        repository.products
    ) == 1


def test_update_product_without_new_image_keeps_existing_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"old-image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    storage.uploads.clear()

    updated = service.update_product(
        product_id=product.id,
        code="OSI-001",
        name="Oso actualizado",
        description="Nueva descripción.",
        price="90000",
        category_id=1,
        is_active=True,
    )

    assert updated.image_url == (
        "https://example.com/products/1.jpg"
    )

    assert storage.uploads == []

    assert storage.deleted == []


def test_update_product_replaces_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"old-image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    old_image_url = product.image_url

    storage.uploads.clear()

    updated = service.update_product(
        product_id=product.id,
        code="OSI-001",
        name="Oso actualizado",
        description="Nueva descripción.",
        price="90000",
        category_id=1,
        image_data=b"new-image",
        image_filename="oso-nuevo.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    new_image_url = updated.image_url

    assert new_image_url == (
        "https://example.com/products/2.jpg"
    )

    assert new_image_url != old_image_url

    assert len(
        storage.uploads
    ) == 1

    assert (
        storage.uploads[0]["file_data"]
        == b"new-image"
    )

    assert storage.deleted == [
        old_image_url
    ]


def test_update_product_deletes_new_image_when_database_update_fails():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"old-image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    old_image_url = product.image_url

    storage.uploads.clear()

    repository.fail_update = True

    with pytest.raises(
        RuntimeError,
        match="Database unavailable",
    ):
        service.update_product(
            product_id=product.id,
            code="OSI-001",
            name="Oso actualizado",
            description="Nueva descripción.",
            price="90000",
            category_id=1,
            image_data=b"new-image",
            image_filename="oso-nuevo.jpg",
            image_content_type="image/jpeg",
            is_active=True,
        )

    assert len(
        storage.uploads
    ) == 1

    new_image_url = (
        storage.uploads[0]["url"]
    )

    assert storage.deleted == [
        new_image_url
    ]

    assert old_image_url != new_image_url

def test_delete_product_removes_product_and_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    image_url = product.image_url

    deleted = service.delete_product(
        product.id
    )

    assert deleted.id == product.id

    assert product.id not in repository.products

    assert storage.deleted == [
        image_url
    ]


def test_delete_product_without_image():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        is_active=True,
    )

    service.delete_product(
        product.id
    )

    assert product.id not in repository.products
    assert storage.deleted == []


def test_remove_product_image_deletes_database_reference_and_storage_file():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    image_url = product.image_url

    updated = service.remove_product_image(
        product.id
    )

    assert updated.image_url is None

    persisted = repository.get_by_id(
        product.id
    )

    assert persisted is not None
    assert persisted.image_url is None

    assert storage.deleted == [
        image_url
    ]


def test_remove_product_image_raises_when_product_does_not_exist():
    (
        service,
        _,
        storage,
    ) = _create_service()

    with pytest.raises(
        LookupError,
        match="El producto no existe.",
    ):
        service.remove_product_image(
            999
        )

    assert storage.deleted == []


def test_remove_product_image_keeps_database_change_when_storage_delete_fails(
    caplog,
):
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    def fail_delete(image_url):
        raise RuntimeError(
            "Storage unavailable"
        )

    storage.delete_product_image = fail_delete

    with caplog.at_level(
        "WARNING"
    ):
        updated = service.remove_product_image(
            product.id
        )

    assert updated.image_url is None

    persisted = repository.get_by_id(
        product.id
    )

    assert persisted is not None
    assert persisted.image_url is None

    assert (
        "Product image cleanup failed"
        in caplog.text
    )

    assert (
        "Storage unavailable"
        not in caplog.text
    )


def test_delete_product_raises_when_product_does_not_exist():
    (
        service,
        _,
        storage,
    ) = _create_service()

    with pytest.raises(
        LookupError,
        match="El producto no existe",
    ):
        service.delete_product(999)

    assert storage.deleted == []

def test_delete_product_keeps_database_deletion_when_image_delete_fails():
    (
        service,
        repository,
        storage,
    ) = _create_service()

    product = service.create_product(
        code="OSI-001",
        name="Amigurumi Oso",
        description="Oso tejido.",
        price="85000",
        category_id=1,
        image_data=b"image",
        image_filename="oso.jpg",
        image_content_type="image/jpeg",
        is_active=True,
    )

    def fail_delete(image_url):
        raise RuntimeError(
            "Storage unavailable"
        )

    storage.delete_product_image = fail_delete

    deleted = service.delete_product(
        product.id
    )

    assert deleted.id == product.id
    assert product.id not in repository.products

def test_cleanup_failure_is_logged_without_replacing_original_error(
    caplog,
):
    (
        service,
        repository,
        storage,
    ) = _create_service()

    existing_product = ProductEntity(
        id=None,
        code="OSI-001",
        name="Producto existente",
        description=None,
        price=Decimal("50000"),
        category_id=1,
        image_url=None,
        is_active=True,
    )

    repository.create(
        existing_product
    )

    storage.fail_delete = True

    with caplog.at_level(
        "WARNING"
    ):
        with pytest.raises(
            DuplicateProductCodeError,
        ):
            service.create_product(
                code="OSI-001",
                name="Otro producto",
                description=None,
                price="85000",
                category_id=1,
                image_data=b"fake-image",
                image_filename="oso.jpg",
                image_content_type="image/jpeg",
                is_active=True,
            )

    assert (
        "Product image cleanup failed"
        in caplog.text
    )

    assert (
        "Storage delete failed"
        not in caplog.text
    )