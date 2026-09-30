from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)


class FakeAdminUserRepository:
    """
    Repositorio de administrador aislado para unit tests.

    Los tests unitarios no deben depender del estado
    persistente de admin_users en SQL Server/PostgreSQL.
    """

    def __init__(
        self,
        user_id=1,
        email="admin@test.com",
        is_active=True,
        token_version=0,
    ):
        self.admin_user = AdminUserEntity(
            id=user_id,
            email=email,
            password_hash="test-password-hash",
            is_active=is_active,
            token_version=token_version,
        )

    def get_by_id(
        self,
        user_id,
    ):
        if (
            self.admin_user is None
            or self.admin_user.id != user_id
        ):
            return None

        return self.admin_user

    def increment_token_version(
        self,
        user_id,
    ):
        if (
            self.admin_user is None
            or self.admin_user.id != user_id
        ):
            return None

        self.admin_user.token_version += 1

        return self.admin_user


def create_isolated_admin_repository():
    """
    Crea un administrador de pruebas completamente aislado.

    El estado inicial siempre es:

        id = 1
        is_active = True
        token_version = 0
    """

    return FakeAdminUserRepository()


def create_unit_auth_headers(
    token_version=0,
):
    """
    Genera un JWT para los unit tests.

    Este token corresponde al administrador aislado
    definido por create_isolated_admin_repository().
    """

    token = (
        JWTService.create_access_token(
            user_id=1,
            email="admin@test.com",
            token_version=token_version,
        )
    )

    return {
        "Authorization": (
            f"Bearer {token}"
        ),
    }