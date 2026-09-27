from abc import ABC, abstractmethod


class StorageRepository(ABC):
    """Contrato para almacenamiento de archivos."""

    @abstractmethod
    def upload(
        self,
        file_data: bytes,
        file_path: str,
        content_type: str,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def delete(
        self,
        file_path: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> None:
        """
        Verifica que el proveedor de almacenamiento
        esté disponible y correctamente configurado.

        Debe lanzar una excepción si el proveedor
        no puede utilizarse correctamente.
        """
        raise NotImplementedError