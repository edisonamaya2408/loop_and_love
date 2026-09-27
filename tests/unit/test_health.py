import app as app_module

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


def test_health_check(client):
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["status"] == "ok"

    assert (
        "environment"
        not in data
    )

    assert (
        "database"
        not in data
    )

    assert (
        "driver"
        not in data
    )


def test_database_health_requires_authentication(
    client,
):
    response = client.get(
        "/health/db"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_REQUIRED"
    )


def test_database_health_does_not_expose_infrastructure_details(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        app_module.db.session,
        "execute",
        lambda statement: None,
    )

    response = client.get(
        "/health/db",
        headers=_authorization_header(),
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert data["status"] == "ok"

    assert (
        "database"
        not in data
    )

    assert (
        "driver"
        not in data
    )

    assert (
        "environment"
        not in data
    )


def test_database_health_returns_generic_error(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        app_module.db.session,
        "execute",
        lambda statement: (
            (_ for _ in ()).throw(
                RuntimeError(
                    "SECRET_DATABASE_CONNECTION_DETAILS"
                )
            )
        ),
    )

    response = client.get(
        "/health/db",
        headers=_authorization_header(),
    )

    assert response.status_code == 500

    data = response.get_json()

    assert data["success"] is False
    assert data["status"] == "error"

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "SECRET_DATABASE_CONNECTION_DETAILS"
        not in response_text
    )