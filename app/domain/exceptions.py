class DomainError(Exception):
    """Excepción base para errores controlados del dominio."""

    pass


class AuthenticationError(DomainError):
    """Indica que las credenciales de autenticación no son válidas."""

    def __init__(self):
        super().__init__(
            "Las credenciales no son válidas."
        )


class DuplicateProductCodeError(DomainError):
    """Indica que el código de producto ya existe."""

    def __init__(self, code: str):
        self.code = code

        super().__init__(
            f"Ya existe un producto con el código {code}"
        )


class DuplicateCategoryNameError(DomainError):
    """Indica que el nombre de categoría ya existe."""

    def __init__(self, name: str):
        self.name = name

        super().__init__(
            f"Ya existe una categoría con el nombre {name}"
        )


class DuplicateCategorySlugError(DomainError):
    """Indica que el slug de categoría ya existe."""

    def __init__(self, slug: str):
        self.slug = slug

        super().__init__(
            f"Ya existe una categoría con el slug {slug}"
        )

class StorageOperationError(DomainError):
    """
    Indica que una operación contra el proveedor de
    almacenamiento no pudo completarse.

    El mensaje expuesto al cliente se mantiene genérico.
    """

    _MESSAGES = {
        "upload": (
            "No fue posible almacenar la imagen "
            "en el servicio de almacenamiento."
        ),
        "delete": (
            "No fue posible eliminar la imagen "
            "del servicio de almacenamiento."
        ),
        "health_check": (
            "No fue posible verificar el servicio "
            "de almacenamiento."
        ),
    }

    def __init__(
        self,
        operation: str,
    ):
        if operation not in self._MESSAGES:
            raise ValueError(
                "Operación de almacenamiento no válida."
            )

        self.operation = operation

        super().__init__(
            self._MESSAGES[operation]
        )