from dataclasses import dataclass


@dataclass(frozen=True)
class PaginationParams:
    """Parámetros validados para paginar resultados."""

    page: int = 1
    per_page: int = 12

    MAX_PER_PAGE = 50

    # Evita offsets excesivamente grandes que puedan provocar
    # consultas innecesariamente costosas.
    MAX_PAGE = 10000

    def __post_init__(self):
        if not isinstance(
            self.page,
            int,
        ) or isinstance(
            self.page,
            bool,
        ):
            raise ValueError(
                "El parámetro page debe ser un número entero."
            )

        if self.page < 1:
            raise ValueError(
                "El parámetro page debe ser mayor que cero."
            )

        if self.page > self.MAX_PAGE:
            raise ValueError(
                "El parámetro page no puede ser mayor que 10000."
            )

        if not isinstance(
            self.per_page,
            int,
        ) or isinstance(
            self.per_page,
            bool,
        ):
            raise ValueError(
                "El parámetro per_page debe ser un número entero."
            )

        if self.per_page < 1:
            raise ValueError(
                "El parámetro per_page debe ser mayor que cero."
            )

        if self.per_page > self.MAX_PER_PAGE:
            raise ValueError(
                "El parámetro per_page no puede ser mayor que 50."
            )

    @classmethod
    def from_values(
        cls,
        page: int | str | None = None,
        per_page: int | str | None = None,
    ):
        """Construye parámetros de paginación desde valores externos."""

        parsed_page = cls._parse_value(
            page,
            "page",
            default=1,
        )

        parsed_per_page = cls._parse_value(
            per_page,
            "per_page",
            default=12,
        )

        return cls(
            page=parsed_page,
            per_page=parsed_per_page,
        )

    @staticmethod
    def _parse_value(
        value,
        parameter_name: str,
        default: int,
    ) -> int:
        if value is None:
            return default

        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                f"El parámetro {parameter_name} "
                "debe ser un número entero."
            )

        if isinstance(
            value,
            int,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            value = value.strip()

            if not value:
                return default

            try:
                return int(value)

            except ValueError as exc:
                raise ValueError(
                    f"El parámetro {parameter_name} "
                    "debe ser un número entero."
                ) from exc

        raise ValueError(
            f"El parámetro {parameter_name} "
            "debe ser un número entero."
        )

    @property
    def offset(self) -> int:
        return (
            self.page - 1
        ) * self.per_page