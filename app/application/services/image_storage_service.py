from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse
from uuid import uuid4
import warnings

from PIL import Image, UnidentifiedImageError

from app.config.settings import Config
from app.domain.repositories.storage_repository import (
    StorageRepository,
)


class ImageStorageService:
    """Caso de uso para validar y almacenar imágenes de productos."""

    ALLOWED_EXTENSIONS = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    ALLOWED_IMAGE_FORMATS = {
        "image/jpeg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
    }

    def __init__(
        self,
        storage_repository: StorageRepository,
    ):
        self.storage_repository = storage_repository

    def upload_product_image(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        """
        Valida y almacena una imagen de producto.

        Devuelve la URL generada por el proveedor
        de almacenamiento.
        """

        self._validate_file_data(
            file_data
        )

        if not isinstance(
            content_type,
            str,
        ):
            raise ValueError(
                "El tipo de imagen no es válido."
            )

        normalized_content_type = (
            content_type.lower().strip()
        )

        extension = self._validate_file(
            filename,
            normalized_content_type,
        )

        self._validate_image_bytes(
            file_data,
            normalized_content_type,
        )

        file_path = self._generate_product_path(
            extension
        )

        return self.storage_repository.upload(
            file_data=file_data,
            file_path=file_path,
            content_type=normalized_content_type,
        )

    def delete_product_image(
        self,
        image_url: str,
    ) -> None:
        """
        Elimina una imagen perteneciente al almacenamiento
        configurado.

        Las URLs que no pertenecen al almacenamiento de
        Loop & Love se ignoran de forma segura.
        """

        if not image_url:
            return

        file_path = self._extract_storage_path(
            image_url
        )

        if file_path:
            self.storage_repository.delete(
                file_path
            )

    @staticmethod
    def _validate_file_data(
        file_data: bytes,
    ) -> None:
        if not isinstance(
            file_data,
            bytes,
        ):
            raise ValueError(
                "Los datos de la imagen no son válidos."
            )

        if not file_data:
            raise ValueError(
                "La imagen está vacía."
            )

        max_size = (
            Config.MAX_IMAGE_SIZE_MB
            * 1024
            * 1024
        )

        if len(file_data) > max_size:
            raise ValueError(
                f"La imagen no puede superar "
                f"los {Config.MAX_IMAGE_SIZE_MB} MB."
            )

    @classmethod
    def _validate_file(
        cls,
        filename: str,
        content_type: str,
    ) -> str:
        if (
            not isinstance(filename, str)
            or not filename.strip()
        ):
            raise ValueError(
                "El nombre de la imagen es obligatorio."
            )

        if not isinstance(
            content_type,
            str,
        ):
            raise ValueError(
                "El tipo de imagen no es válido."
            )

        normalized_content_type = (
            content_type.lower().strip()
        )

        if (
            normalized_content_type
            not in cls.ALLOWED_EXTENSIONS.values()
        ):
            raise ValueError(
                "Formato de imagen no permitido. "
                "Formatos permitidos: JPG, JPEG, PNG y WEBP."
            )

        filename_path = PurePosixPath(
            filename.strip()
        )

        if (
            filename_path.name
            != filename_path.as_posix()
        ):
            raise ValueError(
                "El nombre de la imagen no es válido."
            )

        extension = filename_path.suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Extensión de imagen no permitida. "
                "Formatos permitidos: JPG, JPEG, PNG y WEBP."
            )

        expected_content_type = (
            cls.ALLOWED_EXTENSIONS[extension]
        )

        if (
            normalized_content_type
            != expected_content_type
        ):
            raise ValueError(
                "La extensión de la imagen no coincide "
                "con su tipo MIME."
            )

        return extension

    @classmethod
    def _validate_image_bytes(
        cls,
        file_data: bytes,
        content_type: str,
    ) -> None:
        """
        Comprueba que los bytes realmente correspondan
        a una imagen válida y que su formato interno
        coincida con el MIME declarado.

        La validación se realiza en dos pasos:

        1. verify():
           comprueba la estructura interna del archivo.

        2. load():
           fuerza la decodificación de la imagen.
        """

        expected_format = (
            cls.ALLOWED_IMAGE_FORMATS.get(
                content_type
            )
        )

        if expected_format is None:
            raise ValueError(
                "Formato de imagen no permitido."
            )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    Image.DecompressionBombWarning,
                )

                with Image.open(
                    BytesIO(file_data)
                ) as image:
                    actual_format = (
                        image.format or ""
                    ).upper()

                    if (
                        actual_format
                        != expected_format
                    ):
                        raise ValueError(
                            "El contenido de la imagen "
                            "no coincide con el tipo MIME declarado."
                        )

                    image.verify()

                with Image.open(
                    BytesIO(file_data)
                ) as image:
                    image.load()

        except ValueError:
            raise

        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
            OSError,
        ) as error:
            raise ValueError(
                "Los datos no corresponden a una "
                "imagen válida."
            ) from error

    @staticmethod
    def _generate_product_path(
        extension: str,
    ) -> str:
        return (
            "products/"
            f"{uuid4().hex}"
            f"{extension}"
        )

    @staticmethod
    def _extract_storage_path(
        image_url: str,
    ) -> str | None:
        """
        Convierte una URL propia de almacenamiento en
        una ruta relativa del proveedor.

        Local:
            /static/uploads/products/abc.jpg
            -> products/abc.jpg

        Supabase:
            https://xxx.supabase.co/storage/v1/object/public/
            products/products/abc.jpg
            -> products/abc.jpg
        """

        if not isinstance(
            image_url,
            str,
        ):
            return None

        image_url = image_url.strip()

        if not image_url:
            return None

        local_prefix = "/static/uploads/"

        if image_url.startswith(
            local_prefix
        ):
            file_path = image_url[
                len(local_prefix):
            ]

            return (
                file_path
                if ImageStorageService._is_safe_storage_path(
                    file_path
                )
                else None
            )

        marker = (
            "/storage/v1/object/public/"
        )

        if marker not in image_url:
            return None

        parsed_url = urlparse(
            image_url
        )

        if not parsed_url.scheme:
            return None

        storage_part = parsed_url.path.split(
            marker,
            1,
        )

        if len(storage_part) != 2:
            return None

        storage_part = (
            storage_part[1]
            .lstrip("/")
        )

        bucket_prefix = (
            f"{Config.SUPABASE_STORAGE_BUCKET}/"
        )

        if not storage_part.startswith(
            bucket_prefix
        ):
            return None

        file_path = storage_part[
            len(bucket_prefix):
        ]

        if not ImageStorageService._is_safe_storage_path(
            file_path
        ):
            return None

        return file_path

    @staticmethod
    def _is_safe_storage_path(
        file_path: str,
    ) -> bool:
        if not file_path:
            return False

        path = PurePosixPath(
            file_path
        )

        if path.is_absolute():
            return False

        if ".." in path.parts:
            return False

        return (
            len(path.parts) >= 2
            and path.parts[0] == "products"
        )