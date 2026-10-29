from flask import Blueprint, jsonify, request

from app.application.services.delivery_pricing_service import (
    DeliveryPricingService,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyDeliverySettingsRepository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)


admin_delivery_bp = Blueprint(
    "admin_delivery",
    __name__,
    url_prefix="/api/admin/delivery-settings",
)


def _get_service():
    return DeliveryPricingService(
        SQLAlchemyDeliverySettingsRepository()
    )


def _serialize(settings):
    return {
        "id": settings.id,
        "origin_latitude": (
            str(settings.origin_latitude)
            if settings.origin_latitude is not None
            else None
        ),
        "origin_longitude": (
            str(settings.origin_longitude)
            if settings.origin_longitude is not None
            else None
        ),
        "public_map_center_latitude": (
            str(settings.public_map_center_latitude)
            if settings.public_map_center_latitude is not None
            else None
        ),
        "public_map_center_longitude": (
            str(settings.public_map_center_longitude)
            if settings.public_map_center_longitude is not None
            else None
        ),
        "base_fee": str(settings.base_fee),
        "price_per_km": str(settings.price_per_km),
        "distance_factor": str(settings.distance_factor),
        "max_distance_km": str(settings.max_distance_km),
        "configured": _get_service().is_configured(settings),
        "updated_at": (
            settings.updated_at.isoformat()
            if settings.updated_at
            else None
        ),
    }


@admin_delivery_bp.get("")
@jwt_required
def get_delivery_settings():
    settings = _get_service().get_admin_settings()

    return jsonify({
        "success": True,
        "data": _serialize(settings),
    }), 200


@admin_delivery_bp.put("")
@jwt_required
def update_delivery_settings():
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
        settings = service.save_settings(data)

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_DELIVERY_SETTINGS",
                "message": str(error),
            },
        }), 400

    return jsonify({
        "success": True,
        "data": _serialize(settings),
        "message": "Configuración de domicilio guardada.",
    }), 200