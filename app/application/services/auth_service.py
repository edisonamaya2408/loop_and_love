import re

from app.domain.repositories.admin_user_repository import (
    AdminUserRepository,
)
from app.domain.exceptions import (
    AuthenticationError,
)
from app.domain.normalization import (
    normalize_email,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)


class AuthService:
    """Casos de uso relacionados con autenticación."""

    EMAIL_PATTERN = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    def __init__(
        self,
        repository: AdminUserRepository,
    ):
        self.repository = repository

    def login(
        self,
        email: str,
        password: str,
    ) -> str:
        email = normalize_email(
            email
        )

        if not email:
            raise ValueError(
                "El correo electrónico es obligatorio."
            )

        if not self.EMAIL_PATTERN.match(
            email
        ):
            raise ValueError(
                "El correo electrónico no es válido."
            )

        if not password:
            raise ValueError(
                "La contraseña es obligatoria."
            )

        admin_user = (
            self.repository.get_by_email(
                email
            )
        )

        if admin_user is None:
            raise AuthenticationError()

        if not admin_user.is_active:
            raise AuthenticationError()

        password_valid = (
            PasswordService.verify_password(
                password,
                admin_user.password_hash,
            )
        )

        if not password_valid:
            raise AuthenticationError()

        return JWTService.create_access_token(
            user_id=admin_user.id,
            email=admin_user.email,
            token_version=admin_user.token_version,
        )

    def logout(
        self,
        user_id: int,
    ) -> bool:
        """
        Revoca todos los access tokens actuales del
        administrador incrementando token_version.

        Retorna False si el administrador ya no existe.
        """

        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError(
                "El usuario no es válido."
            )

        revoked_user = (
            self.repository.increment_token_version(
                user_id
            )
        )

        return revoked_user is not None