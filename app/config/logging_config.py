import logging
import logging.config

from flask import g, has_request_context, request


class RequestContextFilter(logging.Filter):
    """Agrega contexto HTTP seguro a cada registro de log."""

    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(
                g,
                "request_id",
                "-",
            )
            record.http_method = request.method
            record.http_path = request.path

        else:
            record.request_id = "-"
            record.http_method = "-"
            record.http_path = "-"

        return True


class AppLogFormatter(logging.Formatter):
    """Formateador consistente para consola local y producción."""

    def format(self, record):
        base_message = super().format(record)

        return (
            f"{base_message} "
            f"request_id={getattr(record, 'request_id', '-')} "
            f"method={getattr(record, 'http_method', '-')} "
            f"path={getattr(record, 'http_path', '-')}"
        )


def configure_logging(log_level: str) -> None:
    """Configura logging centralizado, seguro y compatible con Render."""

    normalized_level = log_level.strip().upper()

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_context": {
                    "()": RequestContextFilter,
                },
            },
            "formatters": {
                "application": {
                    "()": AppLogFormatter,
                    "format": (
                        "%(asctime)s %(levelname)s %(name)s "
                        "%(message)s"
                    ),
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": normalized_level,
                    "formatter": "application",
                    "filters": [
                        "request_context",
                    ],
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "werkzeug": {
                    "level": "WARNING",
                    "propagate": True,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "propagate": True,
                },
            },
            "root": {
                "level": normalized_level,
                "handlers": [
                    "console",
                ],
            },
        }
    )