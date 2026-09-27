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
    def create(
        self,
        admin_user: AdminUserEntity,
    ) -> AdminUserEntity:
        """Crea un usuario administrador."""
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