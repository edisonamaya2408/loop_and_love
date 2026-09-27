import logging
import time
from uuid import uuid4

from flask import Flask, g, request


logger = logging.getLogger(__name__)


def register_request_logging(app: Flask) -> None:
    """Registra contexto y trazabilidad básica de cada request HTTP."""

    @app.before_request
    def start_request():
        g.request_id = uuid4().hex
        g.request_started_at = time.perf_counter()

    @app.after_request
    def finish_request(response):
        started_at = getattr(
            g,
            "request_started_at",
            None,
        )

        if started_at is None:
            duration_ms = 0.0
        else:
            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

        request_id = getattr(
            g,
            "request_id",
            "-",
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        logger.info(
            "HTTP request completed status=%s duration_ms=%.2f",
            response.status_code,
            duration_ms,
        )

        return response