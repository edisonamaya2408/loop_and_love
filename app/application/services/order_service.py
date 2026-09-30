import re
from decimal import Decimal

from app.domain.entities.order import (
    ORDER_STATUS_PENDING,
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

    def create_order(
        self,
        name: str,
        phone: str,
        city: str,
        address: str,
        observations: str | None,
        items,
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
        )

        return self.repository.create(
            order
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