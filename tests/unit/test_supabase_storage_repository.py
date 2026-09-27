import pytest

from app.config.settings import Config
from app.domain.exceptions import (
    StorageOperationError,
)
from app.infrastructure.storage.supabase_storage_repository import (
    SupabaseStorageRepository,
)


class FakeBucket:
    def __init__(self):
        self.upload_calls = []
        self.remove_calls = []
        self.list_calls = []
        self.public_url_calls = []
        self.public_url_error = None
        self.upload_error = None
        self.remove_error = None
        self.list_error = None

    def upload(
        self,
        file,
        path,
        file_options,
    ):
        if self.upload_error is not None:
            raise self.upload_error

        self.upload_calls.append(
            {
                "file": file,
                "path": path,
                "file_options": file_options,
            }
        )

        return {
            "path": path,
        }

    def get_public_url(
        self,
        path,
    ):
        if self.public_url_error is not None:
            raise self.public_url_error

        self.public_url_calls.append(
            path
        )

        return (
            "https://example.supabase.co/"
            "storage/v1/object/public/"
            f"products/{path}"
        )

    def remove(self, paths):
        if self.remove_error is not None:
            raise self.remove_error

        self.remove_calls.append(paths)

        return [
            {
                "name": path,
            }
            for path in paths
        ]

    def list(
        self,
        path,
        options,
    ):
        if self.list_error is not None:
            raise self.list_error

        self.list_calls.append(
            {
                "path": path,
                "options": options,
            }
        )

        return []


class FakeStorage:
    def __init__(self):
        self.bucket = FakeBucket()

    def from_(self, bucket_name):
        return self.bucket


class FakeSupabaseClient:
    def __init__(self):
        self.storage = FakeStorage()


def _create_repository(
    monkeypatch,
):
    fake_client = FakeSupabaseClient()

    monkeypatch.setattr(
        "app.infrastructure.storage.supabase_storage_repository.create_client",
        lambda url, key: fake_client,
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        "test-service-key",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_STORAGE_BUCKET",
        "products",
    )

    repository = SupabaseStorageRepository()

    return repository, fake_client


def test_requires_supabase_url(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        None,
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        "test-service-key",
    )

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_URL no está configurado",
    ):
        SupabaseStorageRepository()


def test_requires_supabase_key(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        None,
    )

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_KEY no está configurado",
    ):
        SupabaseStorageRepository()


def test_upload_uses_expected_supabase_options(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    result = repository.upload(
        file_data=b"fake-image",
        file_path="products/product.jpg",
        content_type="image/jpeg",
    )

    assert result == (
        "https://example.supabase.co"
        "/storage/v1/object/public/"
        "products/products/product.jpg"
    )

    assert client.storage.bucket.upload_calls == [
        {
            "file": b"fake-image",
            "path": "products/product.jpg",
            "file_options": {
                "content-type": "image/jpeg",
                "cache-control": "3600",
                "upsert": False,
            },
        }
    ]

    assert (
        client.storage.bucket.public_url_calls
        == [
            "products/product.jpg",
        ]
    )


def test_delete_removes_expected_path(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    repository.delete(
        "products/product.jpg"
    )

    assert client.storage.bucket.remove_calls == [
        [
            "products/product.jpg",
        ]
    ]


def test_health_check_queries_bucket(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    repository.health_check()

    assert client.storage.bucket.list_calls == [
        {
            "path": "",
            "options": {
                "limit": 1,
                "offset": 0,
            },
        }
    ]


def test_health_check_translates_storage_error(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    client.storage.bucket.list_error = (
        RuntimeError("Supabase unavailable")
    )

    with pytest.raises(
        StorageOperationError,
    ) as exc_info:
        repository.health_check()

    assert (
        exc_info.value.operation
        == "health_check"
    )

    assert (
        exc_info.value.__cause__
        is not None
    )

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )


def test_upload_translates_storage_error(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    client.storage.bucket.upload_error = (
        RuntimeError("Upload failed")
    )

    with pytest.raises(
        StorageOperationError,
    ) as exc_info:
        repository.upload(
            file_data=b"fake-image",
            file_path="products/product.jpg",
            content_type="image/jpeg",
        )

    assert (
        exc_info.value.operation
        == "upload"
    )

    assert (
        str(exc_info.value)
        == (
            "No fue posible almacenar la imagen "
            "en el servicio de almacenamiento."
        )
    )

    assert (
        "Upload failed"
        not in str(exc_info.value)
    )


def test_delete_translates_storage_error(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    client.storage.bucket.remove_error = (
        RuntimeError("Delete failed")
    )

    with pytest.raises(
        StorageOperationError,
    ) as exc_info:
        repository.delete(
            "products/product.jpg"
        )

    assert (
        exc_info.value.operation
        == "delete"
    )

    assert (
        str(exc_info.value)
        == (
            "No fue posible eliminar la imagen "
            "del servicio de almacenamiento."
        )
    )

    assert (
        "Delete failed"
        not in str(exc_info.value)
    )

def test_upload_rejects_path_traversal(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.upload(
            file_data=b"fake-image",
            file_path="../secret.jpg",
            content_type="image/jpeg",
        )

    assert (
        client.storage.bucket.upload_calls
        == []
    )


def test_upload_rejects_non_product_path(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.upload(
            file_data=b"fake-image",
            file_path="avatars/image.jpg",
            content_type="image/jpeg",
        )

    assert (
        client.storage.bucket.upload_calls
        == []
    )


def test_delete_rejects_path_traversal(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.delete(
            "../secret.jpg"
        )

    assert (
        client.storage.bucket.remove_calls
        == []
    )


def test_delete_rejects_non_product_path(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.delete(
            "avatars/image.jpg"
        )

    assert (
        client.storage.bucket.remove_calls
        == []
    )


def test_storage_path_rejects_windows_separator(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.upload(
            file_data=b"fake-image",
            file_path=(
                r"products\image.jpg"
            ),
            content_type="image/jpeg",
        )

    assert (
        client.storage.bucket.upload_calls
        == []
    )

def test_upload_generates_public_url_with_supabase_sdk(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    result = repository.upload(
        file_data=b"fake-image",
        file_path="products/example.webp",
        content_type="image/webp",
    )

    assert (
        client.storage.bucket.public_url_calls
        == [
            "products/example.webp",
        ]
    )

    assert result == (
        "https://example.supabase.co/"
        "storage/v1/object/public/"
        "products/products/example.webp"
    )

def test_upload_translates_public_url_error(
    monkeypatch,
):
    repository, client = _create_repository(
        monkeypatch
    )

    client.storage.bucket.public_url_error = (
        RuntimeError(
            "Public URL generation failed"
        )
    )

    with pytest.raises(
        StorageOperationError,
    ) as exc_info:
        repository.upload(
            file_data=b"fake-image",
            file_path="products/product.jpg",
            content_type="image/jpeg",
        )

    assert (
        exc_info.value.operation
        == "upload"
    )

    assert (
        "Public URL generation failed"
        not in str(exc_info.value)
    )