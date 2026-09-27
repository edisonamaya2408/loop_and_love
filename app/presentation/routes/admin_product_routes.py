from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)
from werkzeug.exceptions import (
    RequestEntityTooLarge,
)

from app.application.services.image_storage_service import (
    ImageStorageService,
)
from app.application.services.product_management_service import (
    ProductManagementService,
)
from app.application.services.product_service import (
    ProductService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyCategoryRepository,
    SQLAlchemyProductRepository,
)
from app.infrastructure.storage.storage_factory import (
    create_storage_repository,
)
from app.presentation.middleware.auth_middleware import jwt_required


admin_products_bp = Blueprint(
    "admin_products",
    __name__,
    url_prefix="/api/admin/products",
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


def _get_product_service():
    return ProductService(
        repository=SQLAlchemyProductRepository(),
        category_repository=SQLAlchemyCategoryRepository(),
    )


def _get_product_management_service():
    return ProductManagementService(
        product_service=_get_product_service(),
        image_storage_service=ImageStorageService(
            create_storage_repository()
        ),
    )


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


def _is_multipart_request():
    content_type = (
        request.content_type or ""
    )

    return content_type.lower().startswith(
        "multipart/form-data"
    )


def _get_multipart_data():
    data = request.form.to_dict()

    if not data:
        return None, (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": (
                            "Los datos del producto "
                            "son obligatorios."
                        ),
                    },
                }
            ),
            400,
        )

    return data, None


def _parse_multipart_is_active(
    data,
    default=None,
):
    value = data.get(
        "is_active",
        default,
    )

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if not isinstance(value, str):
        raise ValueError(
            "El campo is_active debe ser booleano."
        )

    normalized = value.strip().lower()

    if normalized == "true":
        return True

    if normalized == "false":
        return False

    raise ValueError(
        "El campo is_active debe ser booleano."
    )


def _get_image_file():
    image = request.files.get(
        "image"
    )

    if image is None:
        return None

    if not image.filename:
        raise ValueError(
            "La imagen enviada no tiene "
            "un nombre válido."
        )

    return image


def _read_image_data(image):
    if image is None:
        return (
            None,
            None,
            None,
        )

    max_size = (
        int(
            current_app.config[
                "MAX_IMAGE_SIZE_MB"
            ]
        )
        * 1024
        * 1024
    )

    image_data = image.read(
        max_size + 1
    )

    if len(image_data) > max_size:
        raise RequestEntityTooLarge(
            description=(
                "La imagen supera el tamaño máximo permitido "
                f"de {current_app.config['MAX_IMAGE_SIZE_MB']} MB."
            )
        )

    return (
        image_data,
        image.filename,
        image.content_type,
    )


@admin_products_bp.get("/<int:product_id>")
@jwt_required
def get_product(product_id):
    """Obtiene un producto para administración."""

    product = _get_product_service().get_product(
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

    product_response = (
        _get_product_service()
        .to_response(product)
    )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
        }
    ), 200


@admin_products_bp.get("")
@jwt_required
def list_products():
    """Lista productos para administración."""

    result = (
        _get_product_service()
        .list_all_products_paginated(
            search=request.args.get("search"),
            category_id=request.args.get("category_id"),
            min_price=request.args.get("min_price"),
            max_price=request.args.get("max_price"),
            is_active=request.args.get("is_active"),
            page=request.args.get("page"),
            per_page=request.args.get("per_page"),
        )
    )

    products = (
        _get_product_service()
        .to_responses(result.items)
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


@admin_products_bp.post("")
@jwt_required
def create_product():
    """
    Crea un producto.

    Soporta:

        application/json

    y:

        multipart/form-data
    """

    if _is_multipart_request():
        data, error_response = _get_multipart_data()

        if error_response:
            return error_response

        is_active = _parse_multipart_is_active(
            data,
            default="true",
        )

        image = _get_image_file()

        (
            image_data,
            image_filename,
            image_content_type,
        ) = _read_image_data(image)

        management_service = (
            _get_product_management_service()
        )

        product = management_service.create_product(
                code=data.get("code"),
                name=data.get("name"),
                description=data.get("description"),
                price=data.get("price"),
                category_id=data.get("category_id"),
                image_data=image_data,
                image_filename=image_filename,
                image_content_type=image_content_type,
                image_url=data.get("image_url"),
                is_active=is_active,
            )

        product_response = (
            management_service.to_response(
                product
            )
        )

    else:
        data, error_response = _validate_json_body()

        if error_response:
            return error_response

        is_active = data.get(
            "is_active",
            True,
        )

        if not isinstance(
            is_active,
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

        management_service = (
            _get_product_management_service()
        )

        product = management_service.create_product(
                code=data.get("code"),
                name=data.get("name"),
                description=data.get("description"),
                price=data.get("price"),
                category_id=data.get("category_id"),
                image_data=None,
                image_filename=None,
                image_content_type=None,
                image_url=data.get("image_url"),
                is_active=is_active,
            )

        product_response = (
            management_service.to_response(
                product
            )
        )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
        }
    ), 201


@admin_products_bp.put("/<int:product_id>")
@jwt_required
def update_product(product_id):
    """
    Actualiza un producto.

    Soporta:

        application/json

    y:

        multipart/form-data
    """

    if _is_multipart_request():
        data, error_response = _get_multipart_data()

        if error_response:
            return error_response

        if "is_active" not in data:
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": (
                            "El campo is_active es obligatorio "
                            "para actualizar el producto."
                        ),
                    },
                }
            ), 400

        is_active = _parse_multipart_is_active(
            data
        )

        image = _get_image_file()

        (
            image_data,
            image_filename,
            image_content_type,
        ) = _read_image_data(image)

        management_service = (
            _get_product_management_service()
        )

        product = management_service.update_product(
                product_id=product_id,
                code=data.get("code"),
                name=data.get("name"),
                description=data.get("description"),
                price=data.get("price"),
                category_id=data.get("category_id"),
                image_data=image_data,
                image_filename=image_filename,
                image_content_type=image_content_type,
                is_active=is_active,
            )

        product_response = (
            management_service.to_response(
                product
            )
        )

    else:
        data, error_response = _validate_json_body()

        if error_response:
            return error_response

        if "is_active" not in data:
            return jsonify(
                {
                    "success": False,
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": (
                            "El campo is_active es obligatorio "
                            "para actualizar el producto."
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

        management_service = (
            _get_product_management_service()
        )

        product = management_service.update_product(
                product_id=product_id,
                code=data.get("code"),
                name=data.get("name"),
                description=data.get("description"),
                price=data.get("price"),
                category_id=data.get("category_id"),
                image_url=data.get("image_url"),
                is_active=data["is_active"],
            )

        product_response = (
            management_service.to_response(
                product
            )
        )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
        }
    ), 200


@admin_products_bp.patch("/<int:product_id>/status")
@jwt_required
def toggle_product_status(product_id):
    """Activa o inactiva un producto."""

    data, error_response = _validate_json_body()

    if error_response:
        return error_response

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
                        "is_active debe ser booleano."
                    ),
                },
            }
        ), 400

    service = _get_product_service()

    product = service.toggle_product_status(
        product_id=product_id,
        is_active=data["is_active"],
    )

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

@admin_products_bp.delete(
    "/<int:product_id>/image"
)
@jwt_required
def delete_product_image(product_id):
    """
    Elimina únicamente la imagen de un producto.

    El producto y sus demás datos permanecen intactos.
    """

    management_service = (
        _get_product_management_service()
    )

    product = (
        management_service.remove_product_image(
            product_id
        )
    )

    product_response = (
        management_service.to_response(
            product
        )
    )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
            "message": (
                "Imagen del producto eliminada correctamente."
            ),
        }
    ), 200

@admin_products_bp.delete("/<int:product_id>")
@jwt_required
def delete_product(product_id):
    """Elimina un producto para administración."""

    management_service = (
        _get_product_management_service()
    )

    product = management_service.delete_product(
        product_id
    )

    product_response = (
        management_service.to_response(
            product
        )
    )

    return jsonify(
        {
            "success": True,
            "data": _product_to_dict(
                product_response
            ),
            "message": "Producto eliminado correctamente.",
        }
    ), 200