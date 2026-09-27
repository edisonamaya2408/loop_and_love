import logging
import re

import pytest
from flask import Flask, g

import app.presentation.middleware.error_handler as error_handler_module
from app import create_app
from app.config.logging_config import (
    AppLogFormatter,
    RequestContextFilter,
    configure_logging,
)
from app.config.settings import validate_log_level
from app.presentation.middleware.error_handler import (
    register_error_handlers,
)
from app.presentation.middleware.request_logging import (
    register_request_logging,
)


@pytest.mark.parametrize(
    "value",
    [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
        " info ",
        "warning",
    ],
)
def test_validate_log_level_accepts_supported_values(
    value,
):
    result = validate_log_level(value)

    assert result in {
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        " ",
        "TRACE",
        "INVALID",
        10,
        object(),
    ],
)
def test_validate_log_level_rejects_invalid_values(
    value,
):
    with pytest.raises(
        RuntimeError,
        match="LOG_LEVEL no válido",
    ):
        validate_log_level(value)


def test_configure_logging_builds_secure_console_configuration(
    monkeypatch,
):
    captured = {}

    def fake_dict_config(configuration):
        captured["configuration"] = configuration

    monkeypatch.setattr(
        logging.config,
        "dictConfig",
        fake_dict_config,
    )

    configure_logging(" info ")

    configuration = captured["configuration"]

    assert configuration["version"] == 1

    assert (
        configuration["disable_existing_loggers"]
        is False
    )

    assert (
        configuration["root"]["level"]
        == "INFO"
    )

    assert configuration["root"]["handlers"] == [
        "console"
    ]

    console_handler = (
        configuration["handlers"]["console"]
    )

    assert (
        console_handler["class"]
        == "logging.StreamHandler"
    )

    assert (
        console_handler["stream"]
        == "ext://sys.stdout"
    )

    assert (
        console_handler["level"]
        == "INFO"
    )

    assert (
        configuration["loggers"]["werkzeug"]["level"]
        == "WARNING"
    )

    assert (
        configuration["loggers"][
            "sqlalchemy.engine"
        ]["level"]
        == "WARNING"
    )


def test_request_context_filter_adds_safe_request_context():
    app = Flask(__name__)

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Test log message",
        args=(),
        exc_info=None,
    )

    request_filter = RequestContextFilter()

    with app.test_request_context(
        "/health?token=super-secret-value",
        headers={
            "Authorization": "Bearer super-secret-token",
        },
    ):
        g.request_id = "request-123"

        assert request_filter.filter(record) is True

        assert record.request_id == "request-123"
        assert record.http_method == "GET"
        assert record.http_path == "/health"

        assert (
            "super-secret"
            not in record.http_path
        )


def test_request_context_filter_uses_safe_defaults_outside_request():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Test log message",
        args=(),
        exc_info=None,
    )

    request_filter = RequestContextFilter()

    assert request_filter.filter(record) is True

    assert record.request_id == "-"
    assert record.http_method == "-"
    assert record.http_path == "-"


def test_app_log_formatter_includes_request_context():
    record = logging.LogRecord(
        name="loop_and_love",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )

    record.request_id = "request-456"
    record.http_method = "POST"
    record.http_path = "/api/products"

    formatter = AppLogFormatter(
        "%(levelname)s %(name)s %(message)s"
    )

    formatted = formatter.format(record)

    assert "INFO" in formatted
    assert "loop_and_love" in formatted
    assert "HTTP request completed" in formatted
    assert "request_id=request-456" in formatted
    assert "method=POST" in formatted
    assert "path=/api/products" in formatted


def test_app_log_formatter_does_not_include_sensitive_headers():
    app = Flask(__name__)

    record = logging.LogRecord(
        name="loop_and_love",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )

    request_filter = RequestContextFilter()

    with app.test_request_context(
        "/api/products?token=super-secret-token",
        headers={
            "Authorization": (
                "Bearer super-secret-token"
            )
        },
    ):
        g.request_id = "request-789"

        request_filter.filter(record)

        formatter = AppLogFormatter(
            "%(levelname)s %(message)s"
        )

        formatted = formatter.format(record)

    assert "super-secret-token" not in formatted
    assert "Authorization" not in formatted
    assert "Bearer" not in formatted
    assert (
        "path=/api/products"
        in formatted
    )


def test_application_factory_registers_request_id_header(
    client,
):
    response = client.get(
        "/health?token=super-secret-token"
    )

    assert response.status_code == 200

    request_id = response.headers.get(
        "X-Request-ID"
    )

    assert request_id is not None
    assert re.fullmatch(
        r"[0-9a-f]{32}",
        request_id,
    )


def test_application_factory_generates_unique_request_ids(
    client,
):
    first_response = client.get(
        "/health"
    )

    second_response = client.get(
        "/health"
    )

    first_request_id = (
        first_response.headers.get(
            "X-Request-ID"
        )
    )

    second_request_id = (
        second_response.headers.get(
            "X-Request-ID"
        )
    )

    assert first_request_id
    assert second_request_id
    assert (
        first_request_id
        != second_request_id
    )


def test_unexpected_exception_is_logged_without_leaking_details(
    monkeypatch,
):
    captured = {}

    def fake_logger_error(
        message,
        *args,
        **kwargs,
    ):
        captured["message"] = message
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(
        error_handler_module.logger,
        "error",
        fake_logger_error,
    )

    app = Flask(__name__)

    register_error_handlers(app)
    register_request_logging(app)

    @app.get("/test/unexpected-error")
    def unexpected_error():
        raise RuntimeError(
            "SECRET_INTERNAL_ERROR"
        )

    client = app.test_client()

    response = client.get(
        "/test/unexpected-error?secret=secret-value"
    )

    assert response.status_code == 500

    data = response.get_json()

    assert data["success"] is False
    assert (
        data["error"]["code"]
        == "INTERNAL_SERVER_ERROR"
    )

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "SECRET_INTERNAL_ERROR"
        not in response_text
    )

    assert captured["args"] == (
        "RuntimeError",
    )

    exc_info = captured["kwargs"]["exc_info"]

    assert isinstance(
        exc_info,
        tuple,
    )

    assert len(exc_info) == 3
    assert exc_info[0] is RuntimeError
    assert isinstance(
        exc_info[1],
        RuntimeError,
    )
    assert exc_info[1].args == (
        "SECRET_INTERNAL_ERROR",
    )
    assert exc_info[2] is not None