from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from app.application.services.admin_user_service import (
    AdminUserService,
)
from app.domain.exceptions import (
    AdminUserLastActiveError,
    DuplicateAdminUserEmailError,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyAdminUserRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)


admin_users_bp = Blueprint(
    "admin_users",
    __name__,
    url_prefix="/api/admin/users",
)


def _get_admin_user_repository():
    repository = (
        current_app.extensions.get(
            "admin_user_repository"
        )
    )

    if repository is not None:
        return repository

    return SQLAlchemyAdminUserRepository()


def _get_admin_user_service():
    return AdminUserService(
        repository=_get_admin_user_repository()
    )


def _admin_user_to_dict(
    admin_user,
):
    """
    Serializa un administrador sin exponer
    password_hash ni token_version.
    """

    return {
        "id": admin_user.id,
        "name": admin_user.name,
        "email": admin_user.email,
        "is_active": admin_user.is_active,
        "created_at": (
            admin_user.created_at.isoformat()
            if admin_user.created_at
            else None
        ),
        "updated_at": (
            admin_user.updated_at.isoformat()
            if admin_user.updated_at
            else None
        ),
    }


def _validate_json_body():
    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict,
    ):
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": (
                            "El cuerpo de la solicitud "
                            "debe ser JSON."
                        ),
                    },
                }
            ),
            400,
        )

    return data, None


@admin_users_bp.get("")
@jwt_required
def list_admin_users():
    """Lista los usuarios administrativos."""

    users = (
        _get_admin_user_service()
        .list_users()
    )

    return jsonify(
        {
            "success": True,
            "data": [
                _admin_user_to_dict(
                    user
                )
                for user in users
            ],
        }
    ), 200


@admin_users_bp.get(
    "/<int:user_id>"
)
@jwt_required
def get_admin_user(
    user_id,
):
    """Obtiene un usuario administrativo por ID."""

    user = (
        _get_admin_user_service()
        .get_user(
            user_id
        )
    )

    if user is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "ADMIN_USER_NOT_FOUND",
                    "message": (
                        "El administrador no existe."
                    ),
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": _admin_user_to_dict(
                user
            ),
        }
    ), 200


@admin_users_bp.post("")
@jwt_required
def create_admin_user():
    """Crea un nuevo usuario administrativo."""

    data, error_response = (
        _validate_json_body()
    )

    if error_response:
        return error_response

    try:
        user = (
            _get_admin_user_service()
            .create_user(
                name=data.get("name"),
                email=data.get(
                    "email"
                ),
                password=data.get(
                    "password"
                ),
                password_confirmation=(
                    data.get(
                        "password_confirmation"
                    )
                ),
            )
        )

    except DuplicateAdminUserEmailError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": (
                        "ADMIN_USER_EMAIL_ALREADY_EXISTS"
                    ),
                    "message": str(error),
                },
            }
        ), 409

    except ValueError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(error),
                },
            }
        ), 400

    return jsonify(
        {
            "success": True,
            "data": _admin_user_to_dict(
                user
            ),
        }
    ), 201


@admin_users_bp.patch(
    "/<int:user_id>"
)
@jwt_required
def update_admin_user(
    user_id,
):
    """Actualiza un usuario administrativo."""

    data, error_response = (
        _validate_json_body()
    )

    if error_response:
        return error_response

    try:
        user = (
            _get_admin_user_service()
            .update_user(
                user_id=user_id,
                changes=data,
            )
        )

    except DuplicateAdminUserEmailError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": (
                        "ADMIN_USER_EMAIL_ALREADY_EXISTS"
                    ),
                    "message": str(error),
                },
            }
        ), 409

    except AdminUserLastActiveError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": (
                        "ADMIN_USER_LAST_ACTIVE"
                    ),
                    "message": str(error),
                },
            }
        ), 409

    except LookupError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "ADMIN_USER_NOT_FOUND",
                    "message": str(error),
                },
            }
        ), 404

    except ValueError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(error),
                },
            }
        ), 400

    return jsonify(
        {
            "success": True,
            "data": _admin_user_to_dict(
                user
            ),
        }
    ), 200