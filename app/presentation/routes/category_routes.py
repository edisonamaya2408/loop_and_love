from flask import Blueprint, jsonify

from app.application.services.category_service import (
    CategoryService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyCategoryRepository,
)


categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/categories",
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


@categories_bp.get("")
def list_categories():
    """Lista únicamente las categorías activas."""

    categories = (
        _get_category_service()
        .list_active_categories()
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


@categories_bp.get("/<int:category_id>")
def get_category(category_id):
    """Obtiene una categoría activa por ID."""

    category = (
        _get_category_service()
        .get_category(category_id)
    )

    if (
        category is None
        or not category.is_active
    ):
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