from flask import (
    Blueprint,
    g,
    jsonify,
    request,
)

from app.application.services.auth_service import (
    AuthService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyAdminUserRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)
from app.extensions import limiter
from app.infrastructure.security.rate_limit import (
    get_login_account_identifier,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_bp.post("/login")
@limiter.limit(
    "10 per minute"
)
@limiter.limit(
    "5 per minute",
    key_func=get_login_account_identifier,
)
def login():
    """Autentica un usuario administrativo."""

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict,
    ):
        return jsonify(
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
        ), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(
        email,
        str,
    ):
        email = ""

    if not isinstance(
        password,
        str,
    ):
        password = ""

    service = AuthService(
        SQLAlchemyAdminUserRepository()
    )

    token = service.login(
        email=email,
        password=password,
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "access_token": token,
                "token_type": "Bearer",
            },
        }
    ), 200


@auth_bp.post("/logout")
@jwt_required
def logout():
    """Revoca los tokens activos del administrador autenticado."""

    service = AuthService(
        SQLAlchemyAdminUserRepository()
    )

    revoked = service.logout(
        g.authenticated_user["id"]
    )

    if not revoked:
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

    return jsonify(
        {
            "success": True,
            "data": None,
            "message": (
                "Sesión cerrada correctamente."
            ),
        }
    ), 200