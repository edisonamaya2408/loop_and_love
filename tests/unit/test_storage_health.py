from app import create_app
from app.config.settings import Config
from app.infrastructure.security.jwt_service import (
    JWTService,
)


def _authorization_header():
    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def test_storage_health_requires_authentication(
    client,
):
    response = client.get(
        "/health/storage"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_REQUIRED"
    )


def test_storage_health_uses_local_storage_in_development(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "auto",
    )

    monkeypatch.setattr(
        Config,
        "ENVIRONMENT",
        "development",
    )

    app = create_app(
        "development"
    )

    client = app.test_client()

    response = client.get(
        "/health/storage",
        headers=_authorization_header(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["status"] == "ok"

    assert (
        "provider"
        not in data
    )

    assert (
        "environment"
        not in data
    )


def test_storage_health_does_not_expose_storage_details_when_failing(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "local",
    )

    monkeypatch.setattr(
        Config,
        "ENVIRONMENT",
        "development",
    )

    class FailingStorage:
        def health_check(self):
            raise RuntimeError(
                "SECRET_STORAGE_CONNECTION_DETAILS"
            )

    monkeypatch.setattr(
        "app.create_storage_repository",
        lambda: FailingStorage(),
    )

    app = create_app(
        "development"
    )

    client = app.test_client()

    response = client.get(
        "/health/storage",
        headers=_authorization_header(),
    )

    assert response.status_code == 500

    data = response.get_json()

    assert data["success"] is False
    assert data["status"] == "error"

    assert (
        "provider"
        not in data
    )

    assert (
        "environment"
        not in data
    )

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "SECRET_STORAGE_CONNECTION_DETAILS"
        not in response_text
    )