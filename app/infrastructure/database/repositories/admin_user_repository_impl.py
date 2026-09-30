from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.domain.repositories.admin_user_repository import (
    AdminUserRepository,
)
from app.domain.normalization import (
    normalize_email,
)
from app.extensions import db
from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)


class SQLAlchemyAdminUserRepository(
    AdminUserRepository
):
    """Repositorio SQLAlchemy para usuarios administrativos."""

    def __init__(
        self,
        session: Session | None = None,
    ):
        self.session = session or db.session

    @staticmethod
    def _to_entity(
        model: AdminUser,
    ) -> AdminUserEntity:
        return AdminUserEntity(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
            token_version=model.token_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(
        self,
        user_id: int,
    ) -> AdminUserEntity | None:
        model = self.session.get(
            AdminUser,
            user_id,
        )

        if model is None:
            return None

        return self._to_entity(
            model
        )

    def get_by_email(
        self,
        email: str,
    ) -> AdminUserEntity | None:
        normalized_email = normalize_email(
            email
        )

        model = (
            self.session.query(AdminUser)
            .filter(
                AdminUser.email == normalized_email
            )
            .first()
        )

        if model is None:
            return None

        return self._to_entity(
            model
        )

    def count(self) -> int:
        """Devuelve el total de administradores registrados."""

        total = (
            self.session.query(
                func.count(
                    AdminUser.id
                )
            )
            .scalar()
        )

        return int(
            total or 0
        )

    def count_active(self) -> int:
        """Devuelve el total de administradores activos."""

        total = (
            self.session.query(
                func.count(
                    AdminUser.id
                )
            )
            .filter(
                AdminUser.is_active == True
            )
            .scalar()
        )

        return int(
            total or 0
        )

    def list_all(
        self,
    ) -> list[AdminUserEntity]:
        """Lista todos los administradores ordenados por correo."""

        models = (
            self.session.query(AdminUser)
            .order_by(
                AdminUser.email.asc()
            )
            .all()
        )

        return [
            self._to_entity(model)
            for model in models
        ]

    def create(
        self,
        admin_user: AdminUserEntity,
    ) -> AdminUserEntity:
        model = AdminUser(
            email=admin_user.email,
            password_hash=admin_user.password_hash,
            is_active=admin_user.is_active,
            token_version=admin_user.token_version,
        )

        self.session.add(model)
        self.session.commit()

        return self._to_entity(
            model
        )

    def update(
        self,
        admin_user: AdminUserEntity,
        *,
        increment_token_version: bool = False,
    ) -> AdminUserEntity | None:
        """
        Actualiza los datos del administrador.

        Cuando se solicita incremento de token_version,
        la operación se realiza directamente en SQL para
        evitar un read-modify-write no atómico.
        """

        if admin_user.id is None:
            raise ValueError(
                "El ID del administrador es obligatorio."
            )

        values = {
            AdminUser.email: admin_user.email,
            AdminUser.password_hash: admin_user.password_hash,
            AdminUser.is_active: admin_user.is_active,
            AdminUser.updated_at: datetime.now(
                timezone.utc
            ),
        }

        if increment_token_version:
            values[
                AdminUser.token_version
            ] = (
                AdminUser.token_version
                + 1
            )
        else:
            values[
                AdminUser.token_version
            ] = admin_user.token_version

        try:
            updated_rows = (
                self.session.query(
                    AdminUser
                )
                .filter(
                    AdminUser.id == admin_user.id
                )
                .update(
                    values,
                    synchronize_session=False,
                )
            )

            if updated_rows == 0:
                self.session.rollback()
                return None

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return self.get_by_id(
            admin_user.id
        )

    def increment_token_version(
        self,
        user_id: int,
    ) -> AdminUserEntity | None:
        """
        Incrementa token_version directamente en la BD.

        El incremento se realiza en SQL para evitar una
        condición de carrera del tipo read-modify-write.
        """

        try:
            updated_rows = (
                self.session.query(
                    AdminUser
                )
                .filter(
                    AdminUser.id == user_id
                )
                .update(
                    {
                        AdminUser.token_version: (
                            AdminUser.token_version
                            + 1
                        ),
                        AdminUser.updated_at: (
                            datetime.now(
                                timezone.utc
                            )
                        ),
                    },
                    synchronize_session=False,
                )
            )

            if updated_rows == 0:
                self.session.rollback()
                return None

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return self.get_by_id(
            user_id
        )