from flask import Blueprint, jsonify, request

from app.application.services.product_service import ProductService
from app.infrastructure.database.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyProductRepository,
)


products_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products",
)


def _product_to_dict(product):
    return {
        "id": product.id,
        "code": product.code,
        "name": product.name,
        "description": product.description,
        "price": f"{product.price:.2f}",
        "category_id": product.category_id,
        "category": (
            {
                "id": product.category_id,
                "name": product.category_name,
                "slug": product.category_slug,
            }
            if product.category_name is not None
            else None
        ),
        "image_url": product.image_url,
        "is_active": product.is_active,
        "created_at": (
            product.created_at.isoformat()
            if product.created_at
            else None
        ),
        "updated_at": (
            product.updated_at.isoformat()
            if product.updated_at
            else None
        ),
    }


@products_bp.get("")
def list_products():
    """Lista los productos activos del catálogo."""

    service = ProductService(
        repository=SQLAlchemyProductRepository(),
        category_repository=SQLAlchemyCategoryRepository(),
    )

    result = service.list_active_products_paginated(
        search=request.args.get("search"),
        category_id=request.args.get("category_id"),
        min_price=request.args.get("min_price"),
        max_price=request.args.get("max_price"),
        page=request.args.get("page"),
        per_page=request.args.get("per_page"),
    )

    products = service.to_responses(
        result.items
    )

    return jsonify(
        {
            "success": True,
            "data": [
                _product_to_dict(product)
                for product in products
            ],
            "pagination": {
                "page": result.pagination.page,
                "per_page": result.pagination.per_page,
                "total": result.pagination.total,
                "pages": result.pagination.pages,
                "has_next": result.pagination.has_next,
                "has_previous": (
                    result.pagination.has_previous
                ),
            },
        }
    ), 200


@products_bp.get("/<int:product_id>")
def get_product(product_id):
    """Obtiene un producto activo por ID."""

    service = ProductService(
        repository=SQLAlchemyProductRepository(),
        category_repository=SQLAlchemyCategoryRepository(),
    )

    product = service.get_active_product(
        product_id
    )

    if product is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "PRODUCT_NOT_FOUND",
                    "message": "El producto no existe.",
                },
            }
        ), 404

    product_response = service.to_response(
        product
    )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
        }
    ), 200