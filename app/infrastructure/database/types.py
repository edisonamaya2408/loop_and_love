from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator):
    """
    Tipo SQLAlchemy portable para fechas almacenadas en UTC.

    La base de datos almacena el valor sin zona horaria:
        - SQL Server: DATETIME
        - PostgreSQL: TIMESTAMP WITHOUT TIME ZONE

    La aplicación trabaja siempre con datetime aware en UTC.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self,
        value: datetime | None,
        dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc,
            )

        value = value.astimezone(
            timezone.utc,
        )

        return value.replace(
            tzinfo=None,
        )

    def process_result_value(
        self,
        value: datetime | None,
        dialect,
    ) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc,
            )

        return value.astimezone(
            timezone.utc,
        )