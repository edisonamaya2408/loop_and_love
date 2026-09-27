from io import BytesIO

import pytest
from PIL import Image

from app.application.services.image_storage_service import (
    ImageStorageService,
)
from app.config.settings import Config


class FakeStorageRepository:
    def __init__(self):
        self.uploads = []
        self.deleted = []

    def upload(
        self,
        file_data,
        file_path,
        content_type,
    ):
        self.uploads.append(
            {
                "file_data": file_data,
                "file_path": file_path,
                "content_type": content_type,
            }
        )

        return (
            "https://example.com/"
            f"{file_path}"
        )

    def delete(
        self,
        file_path,
    ):
        self.deleted.append(
            file_path
        )


def _create_service():
    repository = FakeStorageRepository()

    service = ImageStorageService(
        repository
    )

    return service, repository


def _create_valid_image_bytes(
    image_format: str,
) -> bytes:
    buffer = BytesIO()

    image = Image.new(
        "RGB",
        (1, 1),
        color=(255, 0, 0),
    )

    image.save(
        buffer,
        format=image_format,
    )

    return buffer.getvalue()


def test_upload_jpeg_image():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "JPEG"
    )

    result = service.upload_product_image(
        file_data=image_data,
        filename="oso.jpg",
        content_type="image/jpeg",
    )

    assert result.startswith(
        "https://example.com/products/"
    )

    assert result.endswith(
        ".jpg"
    )

    assert len(
        repository.uploads
    ) == 1

    upload = repository.uploads[0]

    assert upload["file_data"] == image_data
    assert upload["content_type"] == (
        "image/jpeg"
    )
    assert upload["file_path"].startswith(
        "products/"
    )
    assert upload["file_path"].endswith(
        ".jpg"
    )


def test_upload_jpeg_with_jpeg_extension():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "JPEG"
    )

    result = service.upload_product_image(
        file_data=image_data,
        filename="producto.jpeg",
        content_type="image/jpeg",
    )

    assert result.endswith(
        ".jpeg"
    )

    assert len(
        repository.uploads
    ) == 1


def test_upload_png_image():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "PNG"
    )

    result = service.upload_product_image(
        file_data=image_data,
        filename="producto.png",
        content_type="image/png",
    )

    assert result.endswith(
        ".png"
    )

    assert len(
        repository.uploads
    ) == 1


def test_upload_webp_image():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "WEBP"
    )

    result = service.upload_product_image(
        file_data=image_data,
        filename="producto.webp",
        content_type="image/webp",
    )

    assert result.endswith(
        ".webp"
    )

    assert len(
        repository.uploads
    ) == 1


def test_rejects_unsupported_extension():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="Formato de imagen no permitido",
    ):
        service.upload_product_image(
            file_data=b"fake-data",
            filename="producto.gif",
            content_type="image/gif",
        )


def test_rejects_unsupported_mime_type():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="Formato de imagen no permitido",
    ):
        service.upload_product_image(
            file_data=b"fake-data",
            filename="producto.jpg",
            content_type="image/gif",
        )


def test_rejects_mismatched_extension_and_mime():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="no coincide con su tipo MIME",
    ):
        service.upload_product_image(
            file_data=b"fake-data",
            filename="producto.jpg",
            content_type="image/png",
        )


def test_rejects_fake_image_bytes():
    service, repository = _create_service()

    with pytest.raises(
        ValueError,
        match=(
            "Los datos no corresponden "
            "a una imagen válida"
        ),
    ):
        service.upload_product_image(
            file_data=b"esto no es una imagen",
            filename="producto.jpg",
            content_type="image/jpeg",
        )

    assert repository.uploads == []


def test_rejects_image_with_wrong_internal_format():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "PNG"
    )

    with pytest.raises(
        ValueError,
        match=(
            "no coincide con el tipo MIME declarado"
        ),
    ):
        service.upload_product_image(
            file_data=image_data,
            filename="producto.jpg",
            content_type="image/jpeg",
        )

    assert repository.uploads == []


def test_rejects_corrupted_image_bytes():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "JPEG"
    )

    corrupted_image = image_data[
        :-10
    ]

    with pytest.raises(
        ValueError,
        match=(
            "Los datos no corresponden "
            "a una imagen válida"
        ),
    ):
        service.upload_product_image(
            file_data=corrupted_image,
            filename="producto.jpg",
            content_type="image/jpeg",
        )

    assert repository.uploads == []


def test_accepts_case_insensitive_mime_type():
    service, repository = _create_service()

    image_data = _create_valid_image_bytes(
        "PNG"
    )

    result = service.upload_product_image(
        file_data=image_data,
        filename="producto.png",
        content_type="IMAGE/PNG",
    )

    assert result.endswith(
        ".png"
    )

    assert (
        repository.uploads[0][
            "content_type"
        ]
        == "image/png"
    )


def test_rejects_empty_file():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="La imagen está vacía",
    ):
        service.upload_product_image(
            file_data=b"",
            filename="producto.jpg",
            content_type="image/jpeg",
        )


def test_rejects_path_traversal_filename():
    service, _ = _create_service()

    with pytest.raises(
        ValueError,
        match="nombre de la imagen no es válido",
    ):
        service.upload_product_image(
            file_data=b"fake-data",
            filename="../producto.jpg",
            content_type="image/jpeg",
        )


def test_delete_local_image_extracts_storage_path():
    service, repository = _create_service()

    service.delete_product_image(
        "/static/uploads/products/abc123.jpg"
    )

    assert repository.deleted == [
        "products/abc123.jpg"
    ]


def test_delete_supabase_image_extracts_storage_path():
    service, repository = _create_service()

    service.delete_product_image(
        "https://project.supabase.co/"
        "storage/v1/object/public/"
        "products/products/abc123.jpg"
    )

    assert repository.deleted == [
        "products/abc123.jpg"
    ]


def test_delete_external_url_does_not_touch_storage():
    service, repository = _create_service()

    service.delete_product_image(
        "https://example.com/products/abc123.jpg"
    )

    assert repository.deleted == []


def test_delete_invalid_local_path_does_not_touch_storage():
    service, repository = _create_service()

    service.delete_product_image(
        "/static/uploads/../secrets.txt"
    )

    assert repository.deleted == []


def test_delete_other_storage_path_does_not_touch_storage():
    service, repository = _create_service()

    service.delete_product_image(
        "/static/uploads/other/abc123.jpg"
    )

    assert repository.deleted == []


def test_rejects_image_above_maximum_size():
    service, _ = _create_service()

    max_size = (
        Config.MAX_IMAGE_SIZE_MB
        * 1024
        * 1024
    )

    oversized_image = (
        b"x"
        * (max_size + 1)
    )

    with pytest.raises(
        ValueError,
        match="no puede superar",
    ):
        service.upload_product_image(
            file_data=oversized_image,
            filename="producto.jpg",
            content_type="image/jpeg",
        )