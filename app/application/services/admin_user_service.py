import re

from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.exceptions import (
    AdminUserLastActiveError,
    DuplicateAdminUserEmailError,
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


class AdminUserService:
    """Casos de uso para administrar usuarios administrativos."""

    EMAIL_PATTERN = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    MIN_PASSWORD_LENGTH = 8
    MAX_NAME_LENGTH = 120
    MAX_EMAIL_LENGTH = 255

    _ALLOWED_UPDATE_FIELDS = {
        "name",
        "email",
        "password",
        "password_confirmation",
        "is_active",
    }

    def __init__(
        self,
        repository: AdminUserRepository,
    ):
        self.repository = repository

    def list_users(
        self,
    ) -> list[AdminUserEntity]:
        """Lista todos los administradores."""

        return self.repository.list_all()

    def get_user(
        self,
        user_id: int,
    ) -> AdminUserEntity | None:
        """Obtiene un administrador por ID."""

        self._validate_id(
            user_id
        )

        return self.repository.get_by_id(
            user_id
        )

    def create_user(
        self,
        name: str,
        email: str,
        password: str,
        password_confirmation: str,
    ) -> AdminUserEntity:
        """Crea un nuevo administrador activo."""

        normalized_email = (
            self._validate_email(
                email
            )
        )

        normalized_name = self._validate_name(
            name
        )

        self._validate_password(
            password,
            password_confirmation,
        )

        existing_user = (
            self.repository.get_by_email(
                normalized_email
            )
        )

        if existing_user is not None:
            raise DuplicateAdminUserEmailError(
                normalized_email
            )

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

    def update_user(
        self,
        user_id: int,
        changes: dict,
    ) -> AdminUserEntity:
        """
        Actualiza correo, contraseña y/o estado.

        Cualquier modificación efectiva incrementa
        token_version para invalidar los tokens
        emitidos antes del cambio.
        """

        self._validate_id(
            user_id
        )

        if not isinstance(
            changes,
            dict,
        ):
            raise ValueError(
                "Los cambios del usuario "
                "deben ser un objeto JSON."
            )

        if not changes:
            raise ValueError(
                "Debes indicar al menos un campo "
                "para actualizar."
            )

        unexpected_fields = (
            set(changes)
            - self._ALLOWED_UPDATE_FIELDS
        )

        if unexpected_fields:
            raise ValueError(
                "La solicitud contiene "
                "campos no permitidos."
            )

        user = (
            self.repository.get_by_id(
                user_id
            )
        )

        if user is None:
            raise LookupError(
                "El administrador no existe."
            )

        has_effective_change = False

        if "name" in changes:
            normalized_name = (
                self._validate_name(
                    changes["name"]
                )
            )

            if normalized_name != user.name:
                user.name = normalized_name
                has_effective_change = True

        #has_effective_change = False

        if "email" in changes:
            normalized_email = (
                self._validate_email(
                    changes["email"]
                )
            )

            if normalized_email != user.email:
                existing_user = (
                    self.repository.get_by_email(
                        normalized_email
                    )
                )

                if (
                    existing_user is not None
                    and existing_user.id != user_id
                ):
                    raise DuplicateAdminUserEmailError(
                        normalized_email
                    )

                user.email = normalized_email
                has_effective_change = True

        if "password" in changes:
            password = changes[
                "password"
            ]

            if (
                "password_confirmation"
                not in changes
            ):
                raise ValueError(
                    "La confirmación de la contraseña "
                    "es obligatoria."
                )

            password_confirmation = (
                changes[
                    "password_confirmation"
                ]
            )

            self._validate_password(
                password,
                password_confirmation,
            )

            user.password_hash = (
                PasswordService.hash_password(
                    password
                )
            )

            has_effective_change = True

        elif "password_confirmation" in changes:
            raise ValueError(
                "El campo password_confirmation "
                "solo puede enviarse junto con password."
            )

        if "is_active" in changes:
            is_active = changes[
                "is_active"
            ]

            if not isinstance(
                is_active,
                bool,
            ):
                raise ValueError(
                    "El campo is_active "
                    "debe ser booleano."
                )

            if (
                user.is_active is True
                and is_active is False
            ):
                active_count = (
                    self.repository.count_active()
                )

                if active_count <= 1:
                    raise AdminUserLastActiveError()

            if is_active != user.is_active:
                user.is_active = is_active
                has_effective_change = True

        if not has_effective_change:
            raise ValueError(
                "No hay cambios para aplicar "
                "al administrador."
            )

        updated_user = (
            self.repository.update(
                user,
                increment_token_version=True,
            )
        )

        if updated_user is None:
            raise LookupError(
                "El administrador no existe."
            )

        return updated_user

    @staticmethod
    def _validate_name(
        name: str,
    ) -> str:
        if name is None:
            raise ValueError(
                "El nombre del administrador es obligatorio."
            )

        if not isinstance(name, str):
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
            AdminUserService.MAX_NAME_LENGTH
        ):
            raise ValueError(
                "El nombre del administrador no puede superar "
                f"{AdminUserService.MAX_NAME_LENGTH} caracteres."
            )

        return normalized_name

    @staticmethod
    def _validate_email(
        email: str,
    ) -> str:
        if email is None:
            raise ValueError(
                "El correo electrónico es obligatorio."
            )

        if not isinstance(
            email,
            str,
        ):
            raise ValueError(
                "El correo electrónico debe ser texto."
            )

        normalized_email = normalize_email(
            email
        )

        if not normalized_email:
            raise ValueError(
                "El correo electrónico es obligatorio."
            )

        if len(normalized_email) > (
            AdminUserService.MAX_EMAIL_LENGTH
        ):
            raise ValueError(
                "El correo electrónico no puede superar "
                f"{AdminUserService.MAX_EMAIL_LENGTH} caracteres."
            )

        if not AdminUserService.EMAIL_PATTERN.match(
            normalized_email
        ):
            raise ValueError(
                "El correo electrónico no es válido."
            )

        return normalized_email

    @staticmethod
    def _validate_password(
        password: str,
        password_confirmation: str,
    ) -> None:
        if not isinstance(
            password,
            str,
        ) or not password:
            raise ValueError(
                "La contraseña es obligatoria."
            )

        if not isinstance(
            password_confirmation,
            str,
        ):
            raise ValueError(
                "La confirmación de la contraseña "
                "es obligatoria."
            )

        if len(password) < (
            AdminUserService.MIN_PASSWORD_LENGTH
        ):
            raise ValueError(
                "La contraseña debe tener al menos "
                f"{AdminUserService.MIN_PASSWORD_LENGTH} caracteres."
            )

        if password != password_confirmation:
            raise ValueError(
                "Las contraseñas no coinciden."
            )

    @staticmethod
    def _validate_id(
        user_id: int,
    ) -> None:
        if (
            isinstance(
                user_id,
                bool,
            )
            or not isinstance(
                user_id,
                int,
            )
        ):
            raise ValueError(
                "El ID del administrador "
                "debe ser un número entero."
            )

        if user_id <= 0:
            raise ValueError(
                "El ID del administrador "
                "debe ser mayor que cero."
            )