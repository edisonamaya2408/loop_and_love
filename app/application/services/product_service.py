from decimal import Decimal, InvalidOperation

from app.domain.entities.product import ProductEntity
from app.domain.repositories.product_repository import ProductRepository
from app.domain.exceptions import (
    DuplicateProductCodeError,
)
from app.application.dto.pagination import PaginationParams
from app.application.dto.paginated_result import (
    PaginatedResult,
    PaginationMetadata,
)
from app.domain.repositories.category_repository import (
    CategoryRepository,
)
from app.application.dto.product_response import (
    ProductResponse,
)
from app.domain.normalization import (
    normalize_product_code,
)


class ProductService:
    """Casos de uso relacionados con productos."""

    PRICE_QUANTUM = Decimal(
        "0.01"
    )

    MAX_PRICE = Decimal(
        "9999999999.99"
    )

    def __init__(
        self,
        repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.repository = repository
        self.category_repository = category_repository

    def get_product(
        self,
        product_id: int,
    ) -> ProductEntity | None:

        self._validate_id(product_id)

        return self.repository.get_by_id(product_id)

    def get_active_product(
        self,
        product_id: int,
    ) -> ProductEntity | None:
        """Obtiene un producto únicamente si está activo."""

        self._validate_id(product_id)

        return self.repository.get_active_by_id(
            product_id
        )

    def list_active_products(
        self,
        search: str | None = None,
        category_id: int | str | None = None,
        min_price: str | None = None,
        max_price: str | None = None,
    ) -> list[ProductEntity]:

        minimum = self._parse_price(min_price)
        maximum = self._parse_price(max_price)

        self._validate_price_range(
            minimum,
            maximum,
        )

        parsed_category_id = self._parse_optional_category_id(
            category_id
        )

        self._validate_public_category_filter(
            parsed_category_id
        )

        return self.repository.get_active(
            search=self._clean_text(search),
            category_id=parsed_category_id,
            min_price=minimum,
            max_price=maximum,
        )

    def list_active_products_paginated(
        self,
        search: str | None = None,
        category_id: int | str | None = None,
        min_price: str | None = None,
        max_price: str | None = None,
        page: int | str | None = None,
        per_page: int | str | None = None,
    ) -> PaginatedResult[ProductEntity]:

        pagination = PaginationParams.from_values(
            page=page,
            per_page=per_page,
        )

        minimum = self._parse_price(min_price)
        maximum = self._parse_price(max_price)

        self._validate_price_range(
            minimum,
            maximum,
        )

        parsed_category_id = self._parse_optional_category_id(
            category_id
        )

        self._validate_public_category_filter(
            parsed_category_id
        )

        products, total = (
            self.repository.get_active_paginated(
                search=self._clean_text(search),
                category_id=parsed_category_id,
                min_price=minimum,
                max_price=maximum,
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
            items=products,
            pagination=metadata,
        )

    def list_all_products(self) -> list[ProductEntity]:
        """Obtiene todos los productos para administración."""

        return self.repository.get_all()

    def list_all_products_paginated(
        self,
        search: str | None = None,
        category_id: int | str | None = None,
        min_price: str | None = None,
        max_price: str | None = None,
        is_active: bool | str | None = None,
        page: int | str | None = None,
        per_page: int | str | None = None,
    ) -> PaginatedResult[ProductEntity]:
        """
        Lista productos para administración de forma paginada.
        """

        pagination = PaginationParams.from_values(
            page=page,
            per_page=per_page,
        )

        minimum = self._parse_price(min_price)
        maximum = self._parse_price(max_price)

        self._validate_price_range(
            minimum,
            maximum,
        )

        parsed_category_id = self._parse_optional_category_id(
            category_id
        )

        parsed_is_active = self._parse_optional_bool(
            is_active
        )

        self._validate_admin_category_filter(
            parsed_category_id
        )

        products, total = (
            self.repository.get_all_paginated(
                search=self._clean_text(search),
                category_id=parsed_category_id,
                min_price=minimum,
                max_price=maximum,
                is_active=parsed_is_active,
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
            items=products,
            pagination=metadata,
        )

    def create_product(
        self,
        code: str,
        name: str,
        description: str | None,
        price: str | Decimal,
        category_id: int | str,
        image_url: str | None,
        is_active: bool = True,
    ) -> ProductEntity:

        clean_code = self._validate_code(code)
        clean_name = self._validate_name(name)
        clean_description = self._clean_text(description)
        clean_image_url = self._clean_text(image_url)

        parsed_price = self._parse_required_price(price)

        if self.repository.get_by_code(clean_code) is not None:
            raise DuplicateProductCodeError(
                clean_code
            )

        parsed_category_id = self._validate_category_id(
            category_id
        )

        category = self.category_repository.get_by_id(
            parsed_category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        if not category.is_active:
            raise ValueError(
                "La categoría seleccionada está inactiva."
            )

        product = ProductEntity(
            id=None,
            code=clean_code,
            name=clean_name,
            description=clean_description,
            price=parsed_price,
            category_id=parsed_category_id,
            image_url=clean_image_url,
            is_active=self._validate_is_active(is_active),
        )

        return self.repository.create(product)

    def update_product(
        self,
        product_id: int,
        code: str,
        name: str,
        description: str | None,
        price: str | Decimal,
        category_id: int | str,
        image_url: str | None,
        is_active: bool,
    ) -> ProductEntity:

        self._validate_id(product_id)

        clean_code = self._validate_code(code)

        existing_product = self.repository.get_by_id(
            product_id
        )

        if existing_product is None:
            raise LookupError(
                "El producto no existe."
            )

        parsed_category_id = self._validate_category_id(
            category_id
        )

        category = self.category_repository.get_by_id(
            parsed_category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        if not category.is_active:
            raise ValueError(
                "La categoría seleccionada está inactiva."
            )

        product_with_same_code = self.repository.get_by_code(
            clean_code
        )

        if (
            product_with_same_code is not None
            and product_with_same_code.id != product_id
        ):
            raise DuplicateProductCodeError(
                clean_code
            )

        existing_product.code = clean_code

        existing_product.name = self._validate_name(
            name
        )

        existing_product.description = self._clean_text(
            description
        )

        existing_product.price = (
            self._parse_required_price(price)
        )

        existing_product.category_id = (
            parsed_category_id
        )

        existing_product.image_url = self._clean_text(
            image_url
        )

        existing_product.is_active = (
            self._validate_is_active(is_active)
        )

        return self.repository.update(
            existing_product
        )

    def remove_product_image(
        self,
        product_id: int,
    ) -> tuple[ProductEntity, str]:
        """
        Elimina la referencia de imagen del producto.

        Retorna:
            - producto actualizado
            - URL anterior de la imagen

        El cambio de base de datos se realiza antes de que
        la capa de Storage intente eliminar el archivo físico.
        """

        self._validate_id(
            product_id
        )

        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            raise LookupError(
                "El producto no existe."
            )

        if not product.image_url:
            raise LookupError(
                "El producto no tiene una imagen."
            )

        old_image_url = product.image_url

        product.image_url = None

        updated_product = self.repository.update(
            product
        )

        return (
            updated_product,
            old_image_url,
        )

    def delete_product(
        self,
        product_id: int,
    ) -> ProductEntity:
        """Elimina un producto existente."""

        self._validate_id(product_id)

        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            raise LookupError(
                "El producto no existe."
            )

        deleted_product = self.repository.delete(
            product_id
        )

        if deleted_product is None:
            raise LookupError(
                "El producto no existe."
            )

        return deleted_product

    def toggle_product_status(
        self,
        product_id: int,
        is_active: bool,
    ) -> ProductEntity:

        self._validate_id(product_id)

        product = self.repository.get_by_id(
            product_id
        )

        if product is None:
            raise LookupError(
                "El producto no existe."
            )

        product.is_active = self._validate_is_active(
            is_active
        )

        return self.repository.update(product)

    def _validate_public_category_filter(
        self,
        category_id: int | None,
    ) -> None:
        """Valida una categoría utilizada desde el catálogo público."""

        if category_id is None:
            return

        category = self.category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        if not category.is_active:
            raise LookupError(
                "La categoría no existe."
            )

    def _validate_admin_category_filter(
        self,
        category_id: int | None,
    ) -> None:
        """Valida una categoría utilizada por administración."""

        if category_id is None:
            return

        category = self.category_repository.get_by_id(
            category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

    @staticmethod
    def _build_product_response(
        product: ProductEntity,
        category,
    ) -> ProductResponse:
        """Construye un ProductResponse a partir del producto y su categoría."""

        return ProductResponse(
            id=product.id,
            code=product.code,
            name=product.name,
            description=product.description,
            price=product.price,
            category_id=product.category_id,
            category_name=(
                category.name
                if category is not None
                else None
            ),
            category_slug=(
                category.slug
                if category is not None
                else None
            ),
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    def to_response(
        self,
        product: ProductEntity,
    ) -> ProductResponse:
        """Convierte un producto individual en su DTO de lectura."""

        category = self.category_repository.get_by_id(
            product.category_id
        )

        return self._build_product_response(
            product,
            category,
        )

    def to_responses(
        self,
        products: list[ProductEntity],
    ) -> list[ProductResponse]:
        """
        Convierte múltiples productos evitando consultas
        N+1 contra el repositorio de categorías.
        """

        if not products:
            return []

        category_ids = {
            product.category_id
            for product in products
        }

        categories = (
            self.category_repository.get_by_ids(
                category_ids
            )
        )

        return [
            self._build_product_response(
                product,
                categories.get(
                    product.category_id
                ),
            )
            for product in products
        ]

    @staticmethod
    def _validate_id(product_id: int) -> None:
        if product_id <= 0:
            raise ValueError(
                "El ID del producto debe ser mayor que cero."
            )

    @staticmethod
    def _validate_code(
        code: str,
    ) -> str:
        if not isinstance(code, str):
            raise ValueError(
                "El código del producto es obligatorio."
            )

        code = normalize_product_code(
            code
        )

        if not code:
            raise ValueError(
                "El código del producto es obligatorio."
            )

        if len(code) > 50:
            raise ValueError(
                "El código del producto no puede superar "
                "los 50 caracteres."
            )

        return code

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str):
            raise ValueError(
                "El nombre del producto es obligatorio."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "El nombre del producto es obligatorio."
            )

        if len(name) > 150:
            raise ValueError(
                "El nombre del producto no puede superar "
                "los 150 caracteres."
            )

        return name

    @staticmethod
    def _validate_category_id(
        category_id: int | str,
    ) -> int:
        if isinstance(category_id, bool):
            raise ValueError(
                "El ID de la categoría debe ser un número entero."
            )

        if isinstance(category_id, int):
            parsed_category_id = category_id

        elif isinstance(category_id, str):
            value = category_id.strip()

            if not value:
                raise ValueError(
                    "La categoría es obligatoria."
                )

            try:
                parsed_category_id = int(value)

            except ValueError as exc:
                raise ValueError(
                    "El ID de la categoría debe ser un número entero."
                ) from exc

        else:
            raise ValueError(
                "El ID de la categoría debe ser un número entero."
            )

        if parsed_category_id <= 0:
            raise ValueError(
                "El ID de la categoría debe ser mayor que cero."
            )

        return parsed_category_id

    @staticmethod
    def _parse_optional_category_id(
        category_id: int | str | None,
    ) -> int | None:
        if category_id is None:
            return None

        if isinstance(category_id, str) and not category_id.strip():
            return None

        return ProductService._validate_category_id(
            category_id
        )

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "El valor debe ser texto."
            )

        value = value.strip()

        return value or None

    @classmethod
    def _parse_required_price(
        cls,
        value: str | Decimal,
    ) -> Decimal:
        if isinstance(
            value,
            Decimal,
        ):
            price = value

        elif isinstance(
            value,
            str,
        ):
            try:
                price = Decimal(
                    value.strip()
                )

            except InvalidOperation as exc:
                raise ValueError(
                    "El precio debe ser un número válido."
                ) from exc

        else:
            raise ValueError(
                "El precio debe ser un número válido."
            )

        if not price.is_finite():
            raise ValueError(
                "El precio debe ser un número válido."
            )

        if price <= 0:
            raise ValueError(
                "El precio debe ser mayor que cero."
            )

        if (
            price
            != price.quantize(
                cls.PRICE_QUANTUM
            )
        ):
            raise ValueError(
                "El precio debe tener máximo 2 decimales."
            )

        if price > cls.MAX_PRICE:
            raise ValueError(
                "El precio supera el máximo permitido."
            )

        return price.quantize(
            cls.PRICE_QUANTUM
        )

    @classmethod
    def _parse_price(
        cls,
        value: str | None,
    ) -> Decimal | None:
        if (
            value is None
            or not value.strip()
        ):
            return None

        try:
            price = Decimal(
                value.strip()
            )

        except InvalidOperation as exc:
            raise ValueError(
                "El precio debe ser un número válido."
            ) from exc

        if not price.is_finite():
            raise ValueError(
                "El precio debe ser un número válido."
            )

        if price < 0:
            raise ValueError(
                "El precio no puede ser negativo."
            )

        if (
            price
            != price.quantize(
                cls.PRICE_QUANTUM
            )
        ):
            raise ValueError(
                "El precio debe tener máximo 2 decimales."
            )

        if price > cls.MAX_PRICE:
            raise ValueError(
                "El precio supera el máximo permitido."
            )

        return price.quantize(
            cls.PRICE_QUANTUM
        )

    @staticmethod
    def _validate_price_range(
        minimum: Decimal | None,
        maximum: Decimal | None,
    ) -> None:

        if (
            minimum is not None
            and maximum is not None
            and minimum > maximum
        ):
            raise ValueError(
                "El precio mínimo no puede ser mayor "
                "al precio máximo."
            )

    @staticmethod
    def _parse_optional_bool(
        value: bool | str | None,
    ) -> bool | None:
        """
        Convierte un valor opcional a booleano.

        None significa que no se filtra por estado.
        """

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

    @staticmethod
    def _validate_is_active(value: bool) -> bool:
        """Valida que el estado del producto sea booleano."""

        if not isinstance(value, bool):
            raise ValueError(
                "El campo is_active debe ser booleano."
            )

        return value