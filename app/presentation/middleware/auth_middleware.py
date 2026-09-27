import logging
from functools import wraps

import jwt

from flask import (
    current_app,
    g,
    jsonify,
    request,
)
from sqlalchemy.exc import SQLAlchemyError

from app.infrastructure.database.repositories import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.security.jwt_service import (
    JWTService,
)


logger = logging.getLogger(__name__)


def _get_admin_user_repository():
    """
    Obtiene el repositorio de administradores.

    Permite inyectar un repositorio mediante app.extensions
    para pruebas y mantiene SQLAlchemy como implementación
    predeterminada en producción.
    """

    repository = current_app.extensions.get(
        "admin_user_repository"
    )

    if repository is not None:
        return repository

    return SQLAlchemyAdminUserRepository()


def _authentication_failed():
    """
    Respuesta genérica para credenciales que ya no pueden
    utilizarse.

    No revela si el usuario fue eliminado o desactivado.
    """

    return jsonify(
        {
            "success": False,
            "error": {
                "code": "INVALID_OR_EXPIRED_TOKEN",
                "message": (
                    "El token no es válido o ha expirado."
                ),
            },
        }
    ), 401


def _authentication_unavailable():
    """
    Respuesta genérica cuando no es posible comprobar
    el estado del administrador.
    """

    return jsonify(
        {
            "success": False,
            "error": {
                "code": "AUTHENTICATION_UNAVAILABLE",
                "message": (
                    "No fue posible validar la autenticación "
                    "en este momento."
                ),
            },
        }
    ), 503


def jwt_required(view_function):
    """
    Protege una ruta mediante un JWT enviado como Bearer token.

    Además de validar criptográficamente el token, comprueba
    que el administrador exista y permanezca activo en la BD.
    """

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        authorization = request.headers.get(
            "Authorization"
        )

        if not authorization:
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "AUTHENTICATION_REQUIRED",
                        "message": (
                            "Se requiere autenticación."
                        ),
                    },
                }
            ), 401

        parts = authorization.split()

        if (
            len(parts) != 2
            or parts[0].lower() != "bearer"
        ):
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_AUTHORIZATION_HEADER",
                        "message": (
                            "El encabezado Authorization debe utilizar "
                            "el formato Bearer <token>."
                        ),
                    },
                }
            ), 401

        token = parts[1]

        try:
            payload = (
                JWTService.decode_access_token(
                    token
                )
            )

        except (
            jwt.InvalidTokenError,
            ValueError,
        ):
            return _authentication_failed()

        user_id = int(
            payload["sub"]
        )

        try:
            repository = (
                _get_admin_user_repository()
            )

            admin_user = (
                repository.get_by_id(
                    user_id
                )
            )

        except SQLAlchemyError as error:
            logger.error(
                "Admin authentication state lookup failed "
                "exception_type=%s",
                type(error).__name__,
                exc_info=(
                    type(error),
                    error,
                    error.__traceback__,
                ),
            )

            return _authentication_unavailable()

        if (
            admin_user is None
            or not admin_user.is_active
        ):
            return _authentication_failed()

        if (
            payload["token_version"]
            != admin_user.token_version
        ):
            return _authentication_failed()

        g.authenticated_user = {
            "id": admin_user.id,
            "email": admin_user.email,
        }

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view