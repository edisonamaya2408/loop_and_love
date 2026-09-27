from pathlib import Path

from app.domain.repositories.storage_repository import (
    StorageRepository,
)


class LocalStorageRepository(StorageRepository):
    """Almacenamiento local para desarrollo."""

    def __init__(self):
        self.base_path = (
            Path(__file__).resolve().parents[2]
            / "web"
            / "static"
            / "uploads"
        )

        self.base_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def upload(
        self,
        file_data: bytes,
        file_path: str,
        content_type: str,
    ) -> str:

        destination = self._safe_destination(
            file_path
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination.write_bytes(
            file_data
        )

        return (
            f"/static/uploads/{file_path}"
        )

    def delete(
        self,
        file_path: str,
    ) -> None:

        destination = self._safe_destination(
            file_path
        )

        if destination.exists():
            destination.unlink()

    def health_check(self) -> None:
        """
        Verifica que el almacenamiento local esté disponible.

        Se comprueba que la ruta base exista, sea un directorio
        y permita escritura.
        """

        if not self.base_path.exists():
            raise RuntimeError(
                "El directorio de almacenamiento local no existe."
            )

        if not self.base_path.is_dir():
            raise RuntimeError(
                "La ruta de almacenamiento local no es un directorio."
            )

        test_file = (
            self.base_path
            / ".storage_health_check"
        )

        try:
            test_file.write_text(
                "ok",
                encoding="utf-8",
            )

            test_file.unlink()

        except Exception as error:
            raise RuntimeError(
                "El almacenamiento local no permite escritura."
            ) from error

    def _safe_destination(
        self,
        file_path: str,
    ) -> Path:
        """
        Construye una ruta dentro de base_path.

        Impide traversal y rutas absolutas.
        """

        if not isinstance(
            file_path,
            str,
        ):
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        normalized_path = file_path.strip()

        if not normalized_path:
            raise ValueError(
                "La ruta del archivo no puede estar vacía."
            )

        relative_path = Path(
            normalized_path
        )

        if relative_path.is_absolute():
            raise ValueError(
                "La ruta del archivo no es válida."
            )

        destination = (
            self.base_path
            / relative_path
        )

        base_resolved = (
            self.base_path.resolve()
        )

        destination_resolved = (
            destination.resolve()
        )

        try:
            destination_resolved.relative_to(
                base_resolved
            )

        except ValueError as error:
            raise ValueError(
                "La ruta del archivo no es válida."
            ) from error

        return destination