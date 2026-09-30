from flask import Blueprint, jsonify, request

from app.application.services.order_service import (
    OrderService,
)
from app.extensions import limiter
from app.infrastructure.database.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
)


orders_bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/orders",
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


def _get_json_body():
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


@orders_bp.post("")
@limiter.limit(
    "10 per minute"
)
def create_order():
    """Crea un pedido B2B anónimo a partir del carrito."""

    data, error_response = _get_json_body()

    if error_response is not None:
        return error_response

    order = _get_order_service().create_order(
        name=data.get("name"),
        phone=data.get("phone"),
        city=data.get("city"),
        address=data.get("address"),
        observations=data.get("observations"),
        items=data.get("items"),
    )

    return jsonify(
        {
            "success": True,
            "data": _order_to_dict(
                order
            ),
        }
    ), 201