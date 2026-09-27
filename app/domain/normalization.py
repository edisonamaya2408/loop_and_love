import re
import unicodedata


def normalize_email(value: str) -> str:
    """
    Normaliza un correo electrónico.

    Reglas:
    - Unicode NFKC.
    - elimina espacios exteriores.
    - convierte a minúsculas.
    """

    if not isinstance(value, str):
        raise ValueError(
            "El correo electrónico debe ser texto."
        )

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    return value.strip().lower()


def normalize_product_code(value: str) -> str:
    """
    Normaliza el código de producto.

    Reglas:
    - Unicode NFKC.
    - elimina espacios exteriores.
    - convierte a mayúsculas.
    """

    if not isinstance(value, str):
        raise ValueError(
            "El código del producto debe ser texto."
        )

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    return value.strip().upper()


def normalize_category_display_name(
    value: str,
) -> str:
    """
    Normaliza el nombre visible de una categoría.

    Conserva mayúsculas/minúsculas, pero:
    - aplica Unicode NFKC.
    - elimina espacios exteriores.
    - compacta espacios repetidos.
    """

    if not isinstance(value, str):
        raise ValueError(
            "El nombre de la categoría debe ser texto."
        )

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    return " ".join(
        value.strip().split()
    )


def normalize_category_name(
    value: str,
) -> str:
    """
    Genera la clave canónica de una categoría.

    La clave se usa exclusivamente para:
    - búsquedas.
    - comparación.
    - unicidad.

    No debe utilizarse como nombre visible.
    """

    display_name = normalize_category_display_name(
        value
    )

    return display_name.casefold()


def normalize_slug(value: str) -> str:
    """
    Normaliza un slug existente.
    """

    if not isinstance(value, str):
        raise ValueError(
            "El slug debe ser texto."
        )

    value = unicodedata.normalize(
        "NFKC",
        value,
    )

    return value.strip().lower()