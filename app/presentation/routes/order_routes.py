from flask import Blueprint, jsonify, request

from app.application.services.order_service import (
    OrderService,
)
from app.extensions import limiter
from app.infrastructure.database.repositories import (
    SQLAlchemyOrderRepository,
    SQLAlchemyProductRepository,
)
from app.domain.exceptions import (
    OrderIdempotencyConflictError,
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
        "tracking_token": order.tracking_token,
    }


def _order_tracking_to_dict(order):
    """Devuelve únicamente información no sensible de seguimiento."""

    return {
        "id": order.id,
        "status": order.status,
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
        "status_history": [
            {
                "previous_status": entry.previous_status,
                "new_status": entry.new_status,
                "changed_at": (
                    entry.changed_at.isoformat()
                    if entry.changed_at
                    else None
                ),
            }
            for entry in order.status_history
        ],
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

    service = _get_order_service()

    try:
        order = service.create_order(
            name=data.get("name"),
            phone=data.get("phone"),
            city=data.get("city"),
            address=data.get("address"),
            observations=data.get("observations"),
            items=data.get("items"),
            idempotency_key=request.headers.get(
                "Idempotency-Key"
            ),
        )

    except OrderIdempotencyConflictError as error:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "IDEMPOTENCY_KEY_REUSED",
                    "message": str(error),
                },
            }
        ), 409

    response_status = (
        200
        if getattr(
            order,
            "idempotency_replayed",
            False,
        )
        else 201
    )

    return jsonify(
        {
            "success": True,
            "data": _order_to_dict(order),
        }
    ), response_status


@orders_bp.post("/track")
@limiter.limit("20 per minute")
def track_order():
    """Consulta el estado de un pedido mediante su token secreto."""

    data, error_response = _get_json_body()

    if error_response is not None:
        return error_response

    tracking_token = data.get("tracking_token")

    order = _get_order_service().get_order_tracking(
        tracking_token
    )

    if order is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "ORDER_TRACKING_NOT_FOUND",
                    "message": (
                        "No encontramos un pedido con ese código "
                        "de seguimiento."
                    ),
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": _order_tracking_to_dict(order),
        }
    ), 200

