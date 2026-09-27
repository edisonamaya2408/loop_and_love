import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.domain.exceptions import (
    AuthenticationError,
    DuplicateCategoryNameError,
    DuplicateCategorySlugError,
    DuplicateProductCodeError,
    StorageOperationError,
)
from flask_limiter.errors import (
    RateLimitExceeded,
)


logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Registra los manejadores globales de errores HTTP."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": error.name.upper().replace(" ", "_"),
                    "message": error.description,
                },
            }
        ), error.code

    @app.errorhandler(DuplicateProductCodeError)
    def handle_duplicate_product_code(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "PRODUCT_CODE_ALREADY_EXISTS",
                    "message": str(error),
                },
            }
        ), 409

    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": str(error),
                },
            }
        ), 401

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(error),
                },
            }
        ), 400

    @app.errorhandler(LookupError)
    def handle_lookup_error(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "RESOURCE_NOT_FOUND",
                    "message": str(error),
                },
            }
        ), 404

    @app.errorhandler(StorageOperationError)
    def handle_storage_operation_error(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "STORAGE_UNAVAILABLE",
                    "message": (
                        "No fue posible completar la operación "
                        "de almacenamiento en este momento."
                    ),
                },
            }
        ), 503

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(
            "Error inesperado durante la ejecución de la aplicación. "
            "exception_type=%s",
            type(error).__name__,
            exc_info=(
                type(error),
                error,
                error.__traceback__,
            ),
        )

        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": (
                        "Ocurrió un error interno en el servidor."
                    ),
                },
            }
        ), 500

    @app.errorhandler(DuplicateCategoryNameError)
    def handle_duplicate_category_name(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "CATEGORY_NAME_ALREADY_EXISTS",
                    "message": str(error),
                },
            }
        ), 409

    @app.errorhandler(DuplicateCategorySlugError)
    def handle_duplicate_category_slug(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "CATEGORY_SLUG_ALREADY_EXISTS",
                    "message": str(error),
                },
            }
        ), 409

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(error):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": (
                        "Demasiados intentos. "
                        "Intenta nuevamente más tarde."
                    ),
                },
            }
        ), 429