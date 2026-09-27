from flask import Blueprint, jsonify, request

from app.application.services.category_service import (
    CategoryService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyCategoryRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)


admin_categories_bp = Blueprint(
    "admin_categories",
    __name__,
    url_prefix="/api/admin/categories",
)


def _get_category_service():
    return CategoryService(
        repository=SQLAlchemyCategoryRepository(),
    )


def _category_to_dict(category):
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "is_active": category.is_active,
        "created_at": (
            category.created_at.isoformat()
            if category.created_at
            else None
        ),
        "updated_at": (
            category.updated_at.isoformat()
            if category.updated_at
            else None
        ),
    }


def _validate_json_body():
    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):
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


@admin_categories_bp.get("")
@jwt_required
def list_categories():
    """Lista todas las categorías para administración."""

    categories = (
        _get_category_service()
        .list_all_categories()
    )

    return jsonify(
        {
            "success": True,
            "data": [
                _category_to_dict(category)
                for category in categories
            ],
        }
    ), 200


@admin_categories_bp.get("/<int:category_id>")
@jwt_required
def get_category(category_id):
    """Obtiene cualquier categoría por ID."""

    category = (
        _get_category_service()
        .get_category(category_id)
    )

    if category is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "CATEGORY_NOT_FOUND",
                    "message": "La categoría no existe.",
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": _category_to_dict(category),
        }
    ), 200


@admin_categories_bp.post("")
@jwt_required
def create_category():
    """Crea una nueva categoría."""

    data, error_response = _validate_json_body()

    if error_response:
        return error_response

    category = (
        _get_category_service()
        .create_category(
            name=data.get("name"),
            is_active=data.get(
                "is_active",
                True,
            ),
        )
    )

    return jsonify(
        {
            "success": True,
            "data": _category_to_dict(category),
        }
    ), 201


@admin_categories_bp.put("/<int:category_id>")
@jwt_required
def update_category(category_id):
    """Actualiza una categoría."""

    data, error_response = _validate_json_body()

    if error_response:
        return error_response

    if "name" not in data:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "El campo name es obligatorio."
                    ),
                },
            }
        ), 400

    if "is_active" not in data:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "El campo is_active es obligatorio."
                    ),
                },
            }
        ), 400

    if not isinstance(
        data["is_active"],
        bool,
    ):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "El campo is_active debe ser "
                        "booleano."
                    ),
                },
            }
        ), 400

    category = (
        _get_category_service()
        .update_category(
            category_id=category_id,
            name=data["name"],
            is_active=data["is_active"],
        )
    )

    return jsonify(
        {
            "success": True,
            "data": _category_to_dict(category),
        }
    ), 200


@admin_categories_bp.delete("/<int:category_id>")
@jwt_required
def delete_category(category_id):
    """Elimina una categoría sin productos asociados."""

    category = (
        _get_category_service()
        .delete_category(category_id)
    )

    return jsonify(
        {
            "success": True,
            "data": _category_to_dict(category),
        }
    ), 200