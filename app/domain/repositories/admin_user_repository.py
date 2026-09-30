from abc import ABC, abstractmethod

from app.domain.entities.admin_user import (
    AdminUserEntity,
)


class AdminUserRepository(ABC):
    """Contrato para persistencia de usuarios administrativos."""

    @abstractmethod
    def get_by_id(
        self,
        user_id: int,
    ) -> AdminUserEntity | None:
        """Obtiene un administrador por su identificador."""
        raise NotImplementedError

    @abstractmethod
    def get_by_email(
        self,
        email: str,
    ) -> AdminUserEntity | None:
        """Obtiene un administrador por correo electrónico."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Devuelve el número total de administradores."""
        raise NotImplementedError

    @abstractmethod
    def count_active(self) -> int:
        """Devuelve el número de administradores activos."""
        raise NotImplementedError

    @abstractmethod
    def list_all(
        self,
    ) -> list[AdminUserEntity]:
        """Lista todos los administradores."""
        raise NotImplementedError

    @abstractmethod
    def create(
        self,
        admin_user: AdminUserEntity,
    ) -> AdminUserEntity:
        """Crea un usuario administrador."""
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        admin_user: AdminUserEntity,
        *,
        increment_token_version: bool = False,
    ) -> AdminUserEntity | None:
        """
        Actualiza un usuario administrador.

        Cuando increment_token_version es True, el incremento
        se realiza directamente en la base de datos.
        """
        raise NotImplementedError

    @abstractmethod
    def increment_token_version(
        self,
        user_id: int,
    ) -> AdminUserEntity | None:
        """
        Incrementa atómicamente la versión de tokens
        de un administrador.
        """
        raise NotImplementedError