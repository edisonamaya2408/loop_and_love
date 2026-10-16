import re
import hashlib
import json

from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.domain.exceptions import (
    OrderIdempotencyConflictError,
)

from app.domain.entities.order import (
    ORDER_STATUS_PENDING,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_CANCELLED,
    OrderEntity,
    OrderItemEntity,
)
from app.domain.repositories.order_repository import (
    OrderRepository,
)
from app.domain.repositories.product_repository import (
    ProductRepository,
)


class OrderService:
    """Casos de uso para creación y consulta de pedidos B2B."""

    MAX_ITEMS = 50
    MAX_QUANTITY_PER_ITEM = 99
    MAX_NAME_LENGTH = 150
    MAX_PHONE_LENGTH = 30
    MAX_CITY_LENGTH = 100
    MAX_ADDRESS_LENGTH = 200
    MAX_OBSERVATIONS_LENGTH = 2000

    PHONE_PATTERN = re.compile(
        r"^[0-9+\-().\s]+$"
    )

    def __init__(
        self,
        repository: OrderRepository,
        product_repository: ProductRepository,
    ):
        self.repository = repository
        self.product_repository = product_repository

    
    @staticmethod
    def _normalize_idempotency_key(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "La clave de solicitud no es válida."
            )

        value = value.strip()

        if not value:
            return None

        try:
            return str(UUID(value))
        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError(
                "La clave de solicitud debe ser un UUID válido."
            ) from error

    @staticmethod
    def _build_request_fingerprint(
        *,
        name: str,
        phone: str,
        city: str,
        address: str,
        observations: str | None,
        items: list[dict[str, int]],
    ) -> str:
        canonical_payload = {
            "name": name,
            "phone": phone,
            "city": city,
            "address": address,
            "observations": observations,
            "items": sorted(
                items,
                key=lambda item: item["product_id"],
            ),
        }

        serialized = json.dumps(
            canonical_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _resolve_idempotent_replay(
        existing: OrderEntity,
        request_fingerprint: str,
    ) -> OrderEntity:
        if (
            existing.request_fingerprint
            != request_fingerprint
        ):
            raise OrderIdempotencyConflictError()

        existing.idempotency_replayed = True

        return existing
    

    def create_order(
        self,
        name: str,
        phone: str,
        city: str,
        address: str,
        observations: str | None,
        items,
        *,
        idempotency_key: str | None = None,
    ) -> OrderEntity:
        customer_name = self._validate_text(
            name,
            "El nombre es obligatorio.",
            "El nombre no puede superar los 150 caracteres.",
            self.MAX_NAME_LENGTH,
        )

        clean_phone = self._validate_phone(
            phone
        )

        clean_city = self._validate_text(
            city,
            "La ciudad es obligatoria.",
            "La ciudad no puede superar los 100 caracteres.",
            self.MAX_CITY_LENGTH,
        )

        clean_address = self._validate_text(
            address,
            "La dirección es obligatoria.",
            "La dirección no puede superar los 200 caracteres.",
            self.MAX_ADDRESS_LENGTH,
        )

        clean_observations = self._validate_observations(
            observations
        )

        normalized_items = self._validate_items(
            items
        )

        
        clean_idempotency_key = (
            self._normalize_idempotency_key(
                idempotency_key
            )
        )

        request_fingerprint = None

        if clean_idempotency_key is not None:
            request_fingerprint = (
                self._build_request_fingerprint(
                    name=customer_name,
                    phone=clean_phone,
                    city=clean_city,
                    address=clean_address,
                    observations=clean_observations,
                    items=normalized_items,
                )
            )

            existing_order = (
                self.repository.get_by_idempotency_key(
                    clean_idempotency_key
                )
            )

            if existing_order is not None:
                return self._resolve_idempotent_replay(
                    existing_order,
                    request_fingerprint,
                )


        product_items = []

        for item in normalized_items:
            product = (
                self.product_repository.get_active_by_id(
                    item["product_id"]
                )
            )

            if product is None:
                raise ValueError(
                    "Uno de los productos del pedido "
                    "ya no está disponible."
                )

            line_total = (
                product.price
                * item["quantity"]
            )

            product_items.append(
                OrderItemEntity(
                    id=None,
                    product_id=product.id,
                    product_code=product.code,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=item["quantity"],
                    line_total=line_total,
                )
            )

        total = sum(
            (
                item.line_total
                for item in product_items
            ),
            Decimal("0.00"),
        )

        order = OrderEntity(
            id=None,
            customer_name=customer_name,
            phone=clean_phone,
            city=clean_city,
            address=clean_address,
            observations=clean_observations,
            status=ORDER_STATUS_PENDING,
            total=total,
            items=product_items,
            idempotency_key=clean_idempotency_key,
            request_fingerprint=request_fingerprint,
        )

        
        try:
            return self.repository.create(
                order
            )

        except IntegrityError:
            # Si dos solicitudes con la misma clave llegaron
            # simultáneamente, el índice único evita duplicados.
            # El repositorio revierte la transacción fallida
            # antes de propagar el error.

            if clean_idempotency_key is None:
                raise

            existing_order = (
                self.repository.get_by_idempotency_key(
                    clean_idempotency_key
                )
            )

            if existing_order is None:
                raise

            return self._resolve_idempotent_replay(
                existing_order,
                request_fingerprint,
            )


    def get_order(
        self,
        order_id: int,
    ) -> OrderEntity | None:
        self._validate_id(
            order_id
        )

        return self.repository.get_by_id(
            order_id
        )

    
    def update_admin_order_status(
        self,
        order_id: int,
        status: str,
        *,
        actor_id: int | None = None,
        actor_name: str | None = None,
        actor_email: str | None = None,
    ) -> OrderEntity | None:

        self._validate_id(
            order_id
        )

        clean_status = (
            self._validate_admin_status(
                status
            )
        )

        order = self.repository.get_by_id(
            order_id
        )

        if order is None:
            return None

        current_status = order.status

        if current_status == clean_status:
            raise ValueError(
                "El pedido ya tiene ese estado."
            )

        if current_status != ORDER_STATUS_PENDING:
            raise ValueError(
                "Solo se pueden modificar pedidos pendientes."
            )

        if clean_status not in {
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_CANCELLED,
        }:
            raise ValueError(
                "El estado solicitado no es válido."
            )

        if (
            not isinstance(actor_id, int)
            or isinstance(actor_id, bool)
            or actor_id <= 0
        ):
            clean_actor_id = None
            clean_actor_name = None
            clean_actor_email = None
        else:
            clean_actor_id = actor_id

            clean_actor_name = (
                actor_name.strip()[:120]
                if (
                    isinstance(actor_name, str)
                    and actor_name.strip()
                )
                else None
            )

            clean_actor_email = (
                actor_email.strip()[:255]
                if (
                    isinstance(actor_email, str)
                    and actor_email.strip()
                )
                else None
            )

        return self.repository.update_status(
            order_id,
            clean_status,
            actor_id=clean_actor_id,
            actor_name=clean_actor_name,
            actor_email=clean_actor_email,
        )


    def list_admin_orders(
        self,
        search: str | None = None,
        status: str | None = None,
        page: int | str | None = None,
        per_page: int | str | None = None,
    ):
        from app.application.dto.pagination import (
            PaginationParams,
        )
        from app.application.dto.paginated_result import (
            PaginatedResult,
            PaginationMetadata,
        )

        pagination = (
            PaginationParams.from_values(
                page=page,
                per_page=per_page,
            )
        )

        clean_search = (
            self._clean_text(
                search
            )
        )

        clean_status = (
            self._validate_admin_status(
                status
            )
        )

        orders, total = (
            self.repository.get_all_paginated(
                search=clean_search,
                status=clean_status,
                offset=pagination.offset,
                limit=pagination.per_page,
            )
        )

        metadata = PaginationMetadata(
            page=pagination.page,
            per_page=pagination.per_page,
            total=total,
        )

        return PaginatedResult(
            items=orders,
            pagination=metadata,
        )

    @classmethod
    def _validate_items(
        cls,
        items,
    ) -> list[dict[str, int]]:
        if not isinstance(
            items,
            list,
        ):
            raise ValueError(
                "El campo items debe ser una lista."
            )

        if not items:
            raise ValueError(
                "El pedido debe contener al menos un producto."
            )

        if len(items) > cls.MAX_ITEMS:
            raise ValueError(
                "El pedido no puede contener más de "
                f"{cls.MAX_ITEMS} productos distintos."
            )

        normalized = []
        seen_product_ids = set()

        for item in items:
            if not isinstance(
                item,
                dict,
            ):
                raise ValueError(
                    "Cada producto del pedido debe ser un objeto."
                )

            product_id = (
                cls._validate_positive_integer(
                    item.get("product_id"),
                    "El product_id debe ser un entero mayor que cero.",
                )
            )

            quantity = (
                cls._validate_positive_integer(
                    item.get("quantity"),
                    "La cantidad debe ser un entero mayor que cero.",
                )
            )

            if quantity > cls.MAX_QUANTITY_PER_ITEM:
                raise ValueError(
                    "La cantidad por producto no puede superar "
                    f"{cls.MAX_QUANTITY_PER_ITEM} unidades."
                )

            if product_id in seen_product_ids:
                raise ValueError(
                    "El pedido no puede repetir un mismo producto."
                )

            seen_product_ids.add(
                product_id
            )

            normalized.append(
                {
                    "product_id": product_id,
                    "quantity": quantity,
                }
            )

        return normalized

    @classmethod
    def _validate_phone(
        cls,
        value,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "El teléfono es obligatorio."
            )

        value = " ".join(
            value.strip().split()
        )

        if not value:
            raise ValueError(
                "El teléfono es obligatorio."
            )

        if len(value) > cls.MAX_PHONE_LENGTH:
            raise ValueError(
                "El teléfono no puede superar "
                f"{cls.MAX_PHONE_LENGTH} caracteres."
            )

        if not cls.PHONE_PATTERN.fullmatch(
            value
        ):
            raise ValueError(
                "El teléfono contiene caracteres no válidos."
            )

        digit_count = sum(
            character.isdigit()
            for character in value
        )

        if digit_count < 7:
            raise ValueError(
                "El teléfono debe contener al menos "
                "7 dígitos."
            )

        return value

    @staticmethod
    def _validate_observations(
        value,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "Las observaciones deben ser texto."
            )

        value = value.strip()

        if not value:
            return None

        if len(value) > (
            OrderService.MAX_OBSERVATIONS_LENGTH
        ):
            raise ValueError(
                "Las observaciones no pueden superar "
                f"{OrderService.MAX_OBSERVATIONS_LENGTH} caracteres."
            )

        return value

    @staticmethod
    def _validate_text(
        value,
        required_message: str,
        length_message: str,
        max_length: int,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                required_message
            )

        value = " ".join(
            value.strip().split()
        )

        if not value:
            raise ValueError(
                required_message
            )

        if len(value) > max_length:
            raise ValueError(
                length_message
            )

        return value

    @staticmethod
    def _validate_positive_integer(
        value,
        message: str,
    ) -> int:
        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                message
            )

        if not isinstance(
            value,
            int,
        ):
            raise ValueError(
                message
            )

        if value <= 0:
            raise ValueError(
                message
            )

        return value

    @staticmethod
    def _validate_id(
        order_id: int,
    ) -> None:
        OrderService._validate_positive_integer(
            order_id,
            "El ID del pedido debe ser un entero mayor que cero.",
        )

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "El valor debe ser texto."
            )

        value = value.strip()

        return value or None

    @staticmethod
    def _validate_admin_status(
        value,
    ) -> str | None:

        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            raise ValueError(
                "El estado del pedido no es válido."
            )

        normalized = (
            value.strip().lower()
        )

        allowed_statuses = {
            "pending",
            "confirmed",
            "cancelled",
        }

        if normalized not in allowed_statuses:
            raise ValueError(
                "El estado del pedido no es válido."
            )

        return normalized