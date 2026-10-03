from flask import (
    Blueprint,
    jsonify,
    request,
)

from app.application.services.order_service import (
    OrderService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)


admin_orders_bp = Blueprint(
    "admin_orders",
    __name__,
    url_prefix="/api/admin/orders",
)


def _get_order_service():
    return OrderService(
        repository=SQLAlchemyOrderRepository(),
        product_repository=SQLAlchemyProductRepository(),
    )


def _order_to_dict(order):
    return {
        "id": order.id,
        "name": order.customer_name,
        "phone": order.phone,
        "city": order.city,
        "address": order.address,
        "observations": order.observations,
        "status": order.status,
        "items": [
            {
                "product_id": item.product_id,
                "code": item.product_code,
                "name": item.product_name,
                "unit_price": (
                    f"{item.unit_price:.2f}"
                ),
                "quantity": item.quantity,
                "line_total": (
                    f"{item.line_total:.2f}"
                ),
            }
            for item in order.items
        ],
        "total": f"{order.total:.2f}",
        "created_at": (
            order.created_at.isoformat()
            if order.created_at
            else None
        ),
        "updated_at": (
            order.updated_at.isoformat()
            if order.updated_at
            else None
        ),
    }


@admin_orders_bp.get("/<int:order_id>")
@jwt_required
def get_admin_order(order_id):
    """Obtiene un pedido por ID para administración."""

    order = (
        _get_order_service()
        .get_order(
            order_id
        )
    )

    if order is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "ORDER_NOT_FOUND",
                    "message": "El pedido no existe.",
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": _order_to_dict(
                order
            ),
        }
    ), 200


@admin_orders_bp.patch("/<int:order_id>/status")
@jwt_required
def update_admin_order_status(
    order_id,
):
    payload = request.get_json(
        silent=True
    )

    if not isinstance(
        payload,
        dict,
    ):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": (
                        "El cuerpo de la solicitud "
                        "debe ser un objeto JSON."
                    ),
                },
            }
        ), 400

    status = payload.get(
        "status"
    )

    try:
        order = (
            _get_order_service()
            .update_admin_order_status(
                order_id,
                status,
            )
        )

    except ValueError as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_ORDER_STATUS",
                    "message": str(exc),
                },
            }
        ), 400

    if order is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "ORDER_NOT_FOUND",
                    "message": (
                        "El pedido no existe."
                    ),
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": _order_to_dict(
                order
            ),
        }
    ), 200


@admin_orders_bp.get("")
@jwt_required
def list_admin_orders():
    """Lista pedidos para administración."""

    result = (
        _get_order_service()
        .list_admin_orders(
            search=request.args.get(
                "search"
            ),
            status=request.args.get(
                "status"
            ),
            page=request.args.get(
                "page"
            ),
            per_page=request.args.get(
                "per_page"
            ),
        )
    )

    return jsonify(
        {
            "success": True,
            "data": [
                _order_to_dict(
                    order
                )
                for order in result.items
            ],
            "pagination": {
                "page": (
                    result.pagination.page
                ),
                "per_page": (
                    result.pagination.per_page
                ),
                "total": (
                    result.pagination.total
                ),
                "pages": (
                    result.pagination.pages
                ),
                "has_next": (
                    result.pagination.has_next
                ),
                "has_previous": (
                    result.pagination.has_previous
                ),
            },
        }
    ), 200