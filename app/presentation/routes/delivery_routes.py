from flask import Blueprint, jsonify, request

from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)
from app.domain.exceptions import (
    DeliveryOutsideCoverageError,
    DeliverySettingsNotConfiguredError,
)
from app.extensions import limiter
from app.infrastructure.database.repositories import (
    SQLAlchemyDeliverySettingsRepository,
)


delivery_bp = Blueprint(
    "delivery",
    __name__,
    url_prefix="/api/delivery",
)


def _get_service():
    return DeliveryPricingService(
        SQLAlchemyDeliverySettingsRepository()
    )


@delivery_bp.get("/config")
@limiter.limit("30 per minute")
def get_public_delivery_config():
    service = _get_service()

    try:
        config = service.get_public_map_config()

    except DeliverySettingsNotConfiguredError as error:
        return jsonify({
            "success": False,
            "error": {
                "code": "DELIVERY_NOT_CONFIGURED",
                "message": str(error),
            },
        }), 503

    return jsonify({
        "success": True,
        "data": {
            "map_center_latitude": (
                str(config["map_center_latitude"])
            ),
            "map_center_longitude": (
                str(config["map_center_longitude"])
            ),
            "max_distance_km": str(
                config["max_distance_km"]
            ),
        },
    }), 200


@delivery_bp.post("/quote")
@limiter.limit("20 per minute")
def quote_delivery():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_REQUEST",
                "message": "El cuerpo de la solicitud debe ser JSON.",
            },
        }), 400

    service = _get_service()

    try:
        quote = service.quote(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )

    except DeliverySettingsNotConfiguredError as error:
        return jsonify({
            "success": False,
            "error": {
                "code": "DELIVERY_NOT_CONFIGURED",
                "message": str(error),
            },
        }), 503

    except DeliveryOutsideCoverageError as error:
        return jsonify({
            "success": False,
            "error": {
                "code": "DELIVERY_OUT_OF_COVERAGE",
                "message": str(error),
            },
        }), 422

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_DELIVERY_LOCATION",
                "message": str(error),
            },
        }), 400

    return jsonify({
        "success": True,
        "data": {
            "delivery_fee": str(
                quote["delivery_fee"]
            ),
            "currency": "COP",
        },
    }), 200