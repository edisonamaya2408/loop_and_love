import re
import secrets

from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.exceptions import (
    AdminSetupNotRequiredError,
    AdminSetupUnavailableError,
    InvalidAdminSetupTokenError,
)
from app.domain.normalization import (
    normalize_admin_display_name,
    normalize_email,
)
from app.domain.repositories.admin_user_repository import (
    AdminUserRepository,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)


class AdminSetupService:
    """
    Caso de uso para crear el primer administrador.

    La configuración inicial queda cerrada en cuanto existe
    al menos un registro en admin_users.
    """

    EMAIL_PATTERN = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    MIN_SETUP_TOKEN_LENGTH = 32
    MIN_PASSWORD_LENGTH = 8
    MAX_NAME_LENGTH = 120

    def __init__(
        self,
        repository: AdminUserRepository,
        setup_token: str | None,
    ):
        self.repository = repository
        self.setup_token = setup_token

    def setup_required(self) -> bool:
        """
        Determina si todavía no existe ningún administrador.

        No utiliza APP_ENV. La fuente de verdad es la
        base de datos actualmente utilizada por la aplicación.
        """

        return self.repository.count() == 0

    def _validate_setup_token(
        self,
        provided_token: str,
    ) -> None:
        configured_token = (
            self.setup_token
            if isinstance(
                self.setup_token,
                str,
            )
            else ""
        ).strip()

        if len(
            configured_token.encode(
                "utf-8"
            )
        ) < self.MIN_SETUP_TOKEN_LENGTH:
            raise AdminSetupUnavailableError()

        if not isinstance(
            provided_token,
            str,
        ):
            raise InvalidAdminSetupTokenError()

        if not secrets.compare_digest(
            provided_token,
            configured_token,
        ):
            raise InvalidAdminSetupTokenError()

    @staticmethod
    def _validate_name(
        name: str,
    ) -> str:
        """
        Valida y normaliza el nombre del administrador.
        """

        if name is None:
            raise ValueError(
                "El nombre del administrador es obligatorio."
            )

        if not isinstance(
            name,
            str,
        ):
            raise ValueError(
                "El nombre del administrador debe ser texto."
            )

        normalized_name = (
            normalize_admin_display_name(
                name
            )
        )

        if not normalized_name:
            raise ValueError(
                "El nombre del administrador es obligatorio."
            )

        if len(normalized_name) > (
            AdminSetupService.MAX_NAME_LENGTH
        ):
            raise ValueError(
                "El nombre del administrador no puede superar "
                f"{AdminSetupService.MAX_NAME_LENGTH} caracteres."
            )

        return normalized_name

    def create_initial_admin(
        self,
        setup_token: str,
        name: str,
        email: str,
        password: str,
        password_confirmation: str,
    ) -> AdminUserEntity:
        """
        Crea el primer administrador.

        El método vuelve a comprobar el estado de la base antes
        de crear el usuario para evitar reutilizar el mecanismo
        cuando ya existe administración configurada.
        """

        if not self.setup_required():
            raise AdminSetupNotRequiredError()

        self._validate_setup_token(
            setup_token
        )

        normalized_email = normalize_email(
            email
        )

        normalized_name = self._validate_name(
            name
        )

        if not normalized_email:
            raise ValueError(
                "El correo electrónico es obligatorio."
            )

        if not self.EMAIL_PATTERN.match(
            normalized_email
        ):
            raise ValueError(
                "El correo electrónico no es válido."
            )

        if not isinstance(
            password,
            str,
        ) or not password:
            raise ValueError(
                "La contraseña es obligatoria."
            )

        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise ValueError(
                "La contraseña debe tener al menos "
                f"{self.MIN_PASSWORD_LENGTH} caracteres."
            )

        if password != password_confirmation:
            raise ValueError(
                "Las contraseñas no coinciden."
            )

        existing_user = (
            self.repository.get_by_email(
                normalized_email
            )
        )

        if existing_user is not None:
            raise AdminSetupNotRequiredError()

        # Segunda comprobación inmediatamente antes de crear.
        # Evita reutilizar una pantalla abierta después de que
        # otro administrador haya sido creado.
        if not self.setup_required():
            raise AdminSetupNotRequiredError()

        admin_user = AdminUserEntity(
            id=None,
            name=normalized_name,
            email=normalized_email,
            password_hash=(
                PasswordService.hash_password(
                    password
                )
            ),
            is_active=True,
            token_version=0,
        )

        return self.repository.create(
            admin_user
        )