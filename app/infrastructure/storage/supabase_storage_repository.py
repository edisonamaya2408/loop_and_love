import logging
from pathlib import PurePosixPath

from supabase import create_client

from app.config.settings import Config
from app.domain.exceptions import (
    StorageOperationError,
)
from app.domain.repositories.storage_repository import (
    StorageRepository,
)


logger = logging.getLogger(__name__)


class SupabaseStorageRepository(StorageRepository):
    """Almacenamiento de archivos mediante Supabase Storage."""

    def __init__(self):
        if not Config.SUPABASE_URL:
            raise RuntimeError(
                "SUPABASE_URL no está configurado."
            )

        if not Config.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_KEY no está configurado."
            )

        self.client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY,
        )

        self.bucket_name = (
            Config.SUPABASE_STORAGE_BUCKET
        )

        self.bucket = self.client.storage.from_(
            self.bucket_name
        )

    def upload(
        self,
        file_data: bytes,
        file_path: str,
        content_type: str,
    ) -> str:
        safe_file_path = (
            self._safe_storage_path(
                file_path
            )
        )

        try:
            self.bucket.upload(
                file=file_data,
                path=safe_file_path,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",
                    "upsert": False,
                },
            )

            return self.bucket.get_public_url(
                safe_file_path
            )

        except Exception as error:
            logger.error(
                "Supabase Storage upload failed "
                "exception_type=%s",
                type(error).__name__,
            )

            raise StorageOperationError(
                "upload"
            ) from error

    def delete(
        self,
        file_path: str,
    ) -> None:
        safe_file_path = (
            self._safe_storage_path(
                file_path
            )
        )

        try:
            self.bucket.remove(
                [
                    safe_file_path,
                ]
            )

        except Exception as error:
            logger.error(
                "Supabase Storage delete failed "
                "exception_type=%s",
                type(error).__name__,
            )

            raise StorageOperationError(
                "delete"
            ) from error

    def health_check(self) -> None:
        """
        Verifica que Supabase Storage pueda consultarse.

        No sube, modifica ni elimina archivos.
        """

        try:
            self.bucket.list(
                path="",
                options={
                    "limit": 1,
                    "offset": 0,
                },
            )

        except Exception as error:
            logger.error(
                "Supabase Storage health check failed "
                "exception_type=%s",
                type(error).__name__,
            )

            raise StorageOperationError(
                "health_check"
            ) from error

    @staticmethod
    def _safe_storage_path(
        file_path: str,
    ) -> str:
        """
        Valida que la ruta pertenezca exclusivamente
        al espacio destinado a imágenes de productos.
        """

        if not isinstance(
            file_path,
            str,
        ):
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        normalized_path = (
            file_path.strip()
        )

        if not normalized_path:
            raise ValueError(
                "La ruta del archivo no puede estar vacía."
            )

        if "\\" in normalized_path:
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        path = PurePosixPath(
            normalized_path
        )

        if path.is_absolute():
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        if any(
            part in {
                ".",
                "..",
            }
            for part in path.parts
        ):
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        if (
            path.as_posix()
            != normalized_path
        ):
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        if (
            len(path.parts) < 2
            or path.parts[0] != "products"
        ):
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        return normalized_path