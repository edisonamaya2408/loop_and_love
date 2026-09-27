from flask import Flask

from app.domain.exceptions import (
    AuthenticationError,
)
from app.extensions import limiter
from app.infrastructure.security.rate_limit import (
    get_login_account_identifier,
)
from app.presentation.middleware.error_handler import (
    register_error_handlers,
)
from app.presentation.routes import auth_routes


class FakeAuthService:
    def __init__(
        self,
        error=None,
    ):
        self.error = error

    def login(
        self,
        email,
        password,
    ):
        if self.error is not None:
            raise self.error

        return "fake-token"


class FakeAdminUserRepository:
    pass


def _create_rate_limited_app(
    monkeypatch,
):
    app = Flask(
        __name__
    )

    app.config.update(
        RATELIMIT_ENABLED=True,
        RATELIMIT_STORAGE_URI="memory://",
        RATELIMIT_STRATEGY=(
            "sliding-window-counter"
        ),
        RATELIMIT_HEADERS_ENABLED=False,
        RATELIMIT_KEY_PREFIX=(
            "test-rate-limit"
        ),
    )

    register_error_handlers(
        app
    )

    limiter.init_app(
        app
    )

    service = FakeAuthService(
        error=AuthenticationError()
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

    app.register_blueprint(
        auth_routes.auth_bp
    )

    return app


def test_login_rate_limit_is_applied_per_account(
    monkeypatch,
):
    app = _create_rate_limited_app(
        monkeypatch
    )

    client = app.test_client()

    responses = []

    for _ in range(5):
        responses.append(
            client.post(
                "/api/auth/login",
                json={
                    "email": (
                        "admin@loopandlove.com"
                    ),
                    "password": "wrong",
                },
            )
        )

    assert all(
        response.status_code == 401
        for response in responses
    )

    blocked_response = client.post(
        "/api/auth/login",
        json={
            "email": "admin@loopandlove.com",
            "password": "wrong",
        },
    )

    assert (
        blocked_response.status_code
        == 429
    )

    data = (
        blocked_response.get_json()
    )

    assert data == {
        "success": False,
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": (
                "Demasiados intentos. "
                "Intenta nuevamente más tarde."
            ),
        },
    }


def test_login_rate_limit_is_applied_per_ip(
    monkeypatch,
):
    app = _create_rate_limited_app(
        monkeypatch
    )

    client = app.test_client()

    for index in range(10):
        response = client.post(
            "/api/auth/login",
            json={
                "email": (
                    f"account-{index}"
                    "@loopandlove.com"
                ),
                "password": "wrong",
            },
        )

        assert (
            response.status_code
            == 401
        )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "account-final@loopandlove.com",
            "password": "wrong",
        },
    )

    assert response.status_code == 429


def test_login_account_identifier_hashes_email():
    app = Flask(
        __name__
    )

    with app.test_request_context(
        "/api/auth/login",
        json={
            "email": (
                "Admin@LoopAndLove.com"
            ),
            "password": "secret",
        },
    ):
        identifier = (
            get_login_account_identifier()
        )

    assert identifier.startswith(
        "account:"
    )

    assert (
        "Admin@LoopAndLove.com"
        not in identifier
    )

    assert len(
        identifier
    ) == len(
        "account:"
    ) + 64


def test_invalid_login_payload_is_scoped_to_ip():
    app = Flask(
        __name__
    )

    with app.test_request_context(
        "/api/auth/login",
        json={
            "password": "secret",
        },
    ):
        identifier = (
            get_login_account_identifier()
        )

    assert identifier.startswith(
        "invalid:"
    )