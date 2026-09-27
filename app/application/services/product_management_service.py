import logging

from app.application.services.image_storage_service import (
    ImageStorageService,
)
from app.application.services.product_service import (
    ProductService,
)
from app.domain.entities.product import ProductEntity

logger = logging.getLogger(__name__)

class ProductManagementService:
    """
    Orquesta las operaciones administrativas de productos
    que involucran tanto la base de datos como imágenes.
    """

    def __init__(
        self,
        product_service: ProductService,
        image_storage_service: ImageStorageService,
    ):
        self.product_service = product_service
        self.image_storage_service = image_storage_service

    def to_response(
        self,
        product: ProductEntity,
    ):
        """Convierte un producto en su DTO de respuesta."""

        return self.product_service.to_response(
            product
        )

    def to_responses(
        self,
        products: list[ProductEntity],
    ):
        """Convierte múltiples productos en DTOs de respuesta."""

        return self.product_service.to_responses(
            products
        )

    def create_product(
        self,
        code: str,
        name: str,
        description: str | None,
        price: str,
        category_id: int | str,
        image_data: bytes | None = None,
        image_filename: str | None = None,
        image_content_type: str | None = None,
        image_url: str | None = None,
        is_active: bool = True,
    ) -> ProductEntity:
        """
        Crea un producto y, opcionalmente, su imagen.

        Si la imagen se almacena correctamente pero la creación
        del producto falla, se intenta eliminar la imagen para
        evitar archivos huérfanos.
        """

        uploaded_image_url = None

        try:
            if image_data is not None:
                if image_filename is None:
                    raise ValueError(
                        "El nombre de la imagen es obligatorio."
                    )

                if image_content_type is None:
                    raise ValueError(
                        "El tipo de imagen es obligatorio."
                    )

                uploaded_image_url = (
                    self.image_storage_service.upload_product_image(
                        file_data=image_data,
                        filename=image_filename,
                        content_type=image_content_type,
                    )
                )

                image_url = uploaded_image_url

            return self.product_service.create_product(
                code=code,
                name=name,
                description=description,
                price=price,
                category_id=category_id,
                image_url=image_url,
                is_active=is_active,
            )

        except Exception:
            if uploaded_image_url:
                self._safe_delete_image(
                    uploaded_image_url
                )

            raise

    def update_product(
        self,
        product_id: int,
        code: str,
        name: str,
        description: str | None,
        price: str,
        category_id: int | str,
        image_data: bytes | None = None,
        image_filename: str | None = None,
        image_content_type: str | None = None,
        image_url: str | None = None,
        is_active: bool = True,
    ) -> ProductEntity:
        """
        Actualiza un producto y, opcionalmente, reemplaza su imagen.

        La imagen anterior solamente se elimina después de que
        la actualización de la base de datos haya sido exitosa.
        """

        existing_product = self.product_service.get_product(
            product_id
        )

        if existing_product is None:
            raise LookupError(
                "El producto no existe."
            )

        old_image_url = existing_product.image_url
        new_image_url = None

        try:
            if image_data is not None:
                if image_filename is None:
                    raise ValueError(
                        "El nombre de la imagen es obligatorio."
                    )

                if image_content_type is None:
                    raise ValueError(
                        "El tipo de imagen es obligatorio."
                    )

                new_image_url = (
                    self.image_storage_service.upload_product_image(
                        file_data=image_data,
                        filename=image_filename,
                        content_type=image_content_type,
                    )
                )

                image_url = new_image_url

            elif image_url is None:
                image_url = old_image_url

            updated_product = (
                self.product_service.update_product(
                    product_id=product_id,
                    code=code,
                    name=name,
                    description=description,
                    price=price,
                    category_id=category_id,
                    image_url=image_url,
                    is_active=is_active,
                )
            )

        except Exception:
            if new_image_url:
                self._safe_delete_image(
                    new_image_url
                )

            raise

        if (
            new_image_url
            and old_image_url
            and old_image_url != new_image_url
        ):
            self._safe_delete_image(
                old_image_url
            )

        return updated_product

    def delete_product(
        self,
        product_id: int,
    ) -> ProductEntity:
        """
        Elimina un producto y, si tiene imagen, intenta eliminarla
        del almacenamiento.

        La eliminación de la imagen se realiza después de que
        la eliminación de la base de datos haya sido exitosa.
        """

        product = self.product_service.get_product(
            product_id
        )

        if product is None:
            raise LookupError(
                "El producto no existe."
            )

        deleted_product = (
            self.product_service.delete_product(
                product_id
            )
        )

        if deleted_product.image_url:
            self._safe_delete_image(
                deleted_product.image_url
            )

        return deleted_product

    def remove_product_image(
        self,
        product_id: int,
    ) -> ProductEntity:
        """
        Elimina la imagen asociada a un producto.

        Primero elimina la referencia de la imagen en la base
        de datos y posteriormente intenta eliminar el archivo
        del proveedor de almacenamiento.

        Si la limpieza del Storage falla, la operación de base
        de datos se conserva y el fallo queda registrado.
        """

        (
            updated_product,
            old_image_url,
        ) = self.product_service.remove_product_image(
            product_id
        )

        self._safe_delete_image(
            old_image_url
        )

        return updated_product

    def delete_product_image(
        self,
        image_url: str | None,
    ) -> None:
        """Elimina una imagen de producto de forma segura."""

        if not image_url:
            return

        self._safe_delete_image(
            image_url
        )

    def _safe_delete_image(
        self,
        image_url: str,
    ) -> None:
        """
        Intenta eliminar una imagen.

        Una falla durante la limpieza no reemplaza la
        excepción original de creación o actualización,
        pero queda registrada para diagnóstico.
        """

        try:
            self.image_storage_service.delete_product_image(
                image_url
            )

        except Exception as error:
            logger.warning(
                "Product image cleanup failed "
                "exception_type=%s",
                type(error).__name__,
            )