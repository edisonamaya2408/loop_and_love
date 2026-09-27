from pathlib import Path

import pytest

from app.infrastructure.storage.local_storage_repository import (
    LocalStorageRepository,
)


def _create_repository(
    tmp_path,
):
    repository = LocalStorageRepository()

    repository.base_path = (
        tmp_path / "uploads"
    )

    repository.base_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return repository


def test_upload_creates_file(
    tmp_path,
):
    repository = _create_repository(
        tmp_path
    )

    result = repository.upload(
        file_data=b"image-data",
        file_path="products/test.jpg",
        content_type="image/jpeg",
    )

    expected_file = (
        repository.base_path
        / "products"
        / "test.jpg"
    )

    assert expected_file.exists()
    assert expected_file.read_bytes() == (
        b"image-data"
    )

    assert result == (
        "/static/uploads/products/test.jpg"
    )


def test_delete_removes_file(
    tmp_path,
):
    repository = _create_repository(
        tmp_path
    )

    repository.upload(
        file_data=b"image-data",
        file_path="products/test.jpg",
        content_type="image/jpeg",
    )

    repository.delete(
        "products/test.jpg"
    )

    expected_file = (
        repository.base_path
        / "products"
        / "test.jpg"
    )

    assert not expected_file.exists()


def test_upload_rejects_path_traversal(
    tmp_path,
):
    repository = _create_repository(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.upload(
            file_data=b"image-data",
            file_path="../outside.jpg",
            content_type="image/jpeg",
        )


def test_delete_rejects_path_traversal(
    tmp_path,
):
    repository = _create_repository(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.delete(
            "../outside.jpg"
        )


def test_upload_rejects_absolute_path(
    tmp_path,
):
    repository = _create_repository(
        tmp_path
    )

    absolute_path = (
        Path(tmp_path)
        / "outside.jpg"
    )

    with pytest.raises(
        ValueError,
        match="ruta del archivo no es válida",
    ):
        repository.upload(
            file_data=b"image-data",
            file_path=str(
                absolute_path
            ),
            content_type="image/jpeg",
        )