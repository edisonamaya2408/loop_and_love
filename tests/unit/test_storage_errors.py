from flask import Flask

from app.domain.exceptions import (
    StorageOperationError,
)
from app.presentation.middleware.error_handler import (
    register_error_handlers,
)


def test_storage_operation_error_exposes_safe_message():
    error = StorageOperationError(
        "upload"
    )

    assert error.operation == "upload"

    assert str(error) == (
        "No fue posible almacenar la imagen "
        "en el servicio de almacenamiento."
    )


def test_storage_operation_error_rejects_invalid_operation():
    try:
        StorageOperationError(
            "invalid-operation"
        )

        assert False, (
            "Se esperaba ValueError"
        )

    except ValueError as error:
        assert (
            "Operación de almacenamiento "
            "no válida."
            in str(error)
        )


def test_storage_operation_error_returns_503():
    app = Flask(__name__)

    register_error_handlers(app)

    @app.get("/test/storage-error")
    def storage_error():
        raise StorageOperationError(
            "upload"
        )

    client = app.test_client()

    response = client.get(
        "/test/storage-error"
    )

    assert response.status_code == 503

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "STORAGE_UNAVAILABLE"
    )

    assert (
        data["error"]["message"]
        == (
            "No fue posible completar la operación "
            "de almacenamiento en este momento."
        )
    )


def test_storage_operation_error_never_exposes_provider_details():
    app = Flask(__name__)

    register_error_handlers(app)

    @app.get("/test/storage-error")
    def storage_error():
        try:
            raise RuntimeError(
                "SUPABASE_INTERNAL_SECRET"
            )

        except RuntimeError as original_error:
            raise StorageOperationError(
                "upload"
            ) from original_error

    client = app.test_client()

    response = client.get(
        "/test/storage-error"
    )

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "SUPABASE_INTERNAL_SECRET"
        not in response_text
    )

    assert (
        "RuntimeError"
        not in response_text
    )

    assert response.status_code == 503