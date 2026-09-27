import pytest

from app import create_app
from app.presentation.routes import auth_routes
from app.domain.exceptions import (
    AuthenticationError,
)


class FakeAuthService:
    def __init__(
        self,
        token="fake-access-token",
        error=None,
    ):
        self.token = token
        self.error = error
        self.login_calls = []

    def login(
        self,
        email,
        password,
    ):
        self.login_calls.append(
            {
                "email": email,
                "password": password,
            }
        )

        if self.error is not None:
            raise self.error

        return self.token


class FakeAdminUserRepository:
    pass


def _create_test_app(monkeypatch):
    app = create_app("development")

    service = FakeAuthService()

    monkeypatch.setattr(
        auth_routes,
        "AuthService",
        lambda repository: service,
    )

    monkeypatch.setattr(
        auth_routes,
        "SQLAlchemyAdminUserRepository",
        lambda: FakeAdminUserRepository(),
    )

    return app, service


def test_login_returns_access_token(
    monkeypatch,
):
    app, service = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@loopandlove.com",
            "password": "Password123!",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"] == {
        "access_token": "fake-access-token",
        "token_type": "Bearer",
    }

    assert service.login_calls == [
        {
            "email": "admin@loopandlove.com",
            "password": "Password123!",
        }
    ]


def test_login_rejects_non_json_body(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        data="texto plano",
        content_type="text/plain",
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data == {
        "success": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": (
                "El cuerpo de la solicitud debe ser JSON."
            ),
        },
    }


def test_login_rejects_json_array(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json=[
            {
                "email": "admin@loopandlove.com",
                "password": "Password123!",
            }
        ],
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data == {
        "success": False,
        "error": {
            "code": "INVALID_REQUEST",
            "message": (
                "El cuerpo de la solicitud debe ser JSON."
            ),
        },
    }


def test_login_converts_missing_fields_to_empty_strings(
    monkeypatch,
):
    app, service = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={},
    )

    assert response.status_code == 200

    assert service.login_calls == [
        {
            "email": "",
            "password": "",
        }
    ]

def test_login_returns_same_generic_response_for_authentication_failure(
    monkeypatch,
):
    service = FakeAuthService(
        error=AuthenticationError()
    )

    app = create_app(
        "development"
    )

    monkeypatch.setattr(
        auth_routes,
        "AuthService",
        lambda repository: service,
    )

    monkeypatch.setattr(
        auth_routes,
        "SQLAlchemyAdminUserRepository",
        lambda: FakeAdminUserRepository(),
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@loopandlove.com",
            "password": "wrong",
        },
    )

    assert response.status_code == 401

    assert response.get_json() == {
        "success": False,
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": (
                "Las credenciales no son válidas."
            ),
        },
    }

def test_login_authentication_error_does_not_expose_account_state(
    monkeypatch,
):
    service = FakeAuthService(
        error=AuthenticationError()
    )

    app = create_app(
        "development"
    )

    monkeypatch.setattr(
        auth_routes,
        "AuthService",
        lambda repository: service,
    )

    monkeypatch.setattr(
        auth_routes,
        "SQLAlchemyAdminUserRepository",
        lambda: FakeAdminUserRepository(),
    )

    client = app.test_client()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "inactive@loopandlove.com",
            "password": "wrong",
        },
    )

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "inactivo"
        not in response_text.lower()
    )

    assert (
        "no existe"
        not in response_text.lower()
    )

    data = response.get_json()

    assert data["error"]["message"] == (
        "Las credenciales no son válidas."
    )

    assert (
        data["error"]["code"]
        == "INVALID_CREDENTIALS"
    )

    assert response.status_code == 401