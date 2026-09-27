from datetime import datetime, timedelta, timezone

import jwt
import pytest

from flask import (
    g,
    jsonify,
)
from sqlalchemy.exc import (
    SQLAlchemyError,
)

from app.domain.entities.admin_user import (
    AdminUserEntity,
)
from app.presentation.middleware import (
    auth_middleware,
)

from app import create_app
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)
from app.config.settings import Config
from app.infrastructure.security.jwt_service import (
    JWTService,
)

class FakeAdminUserRepository:
    def __init__(
        self,
        admin_user=None,
        error=None,
    ):
        self.admin_user = admin_user
        self.error = error
        self.get_by_id_calls = []

    def get_by_id(
        self,
        user_id,
    ):
        self.get_by_id_calls.append(
            user_id
        )

        if self.error is not None:
            raise self.error

        if (
            self.admin_user is None
            or self.admin_user.id != user_id
        ):
            return None

        return self.admin_user


def _create_protected_app(
    admin_user=None,
    repository=None,
):
    app = create_app(
        "development"
    )

    if repository is None:
        if admin_user is None:
            admin_user = AdminUserEntity(
                id=1,
                email="admin@loopandlove.com",
                password_hash="test-hash",
                is_active=True,
            )

        repository = (
            FakeAdminUserRepository(
                admin_user=admin_user
            )
        )

    app.extensions[
        "admin_user_repository"
    ] = repository

    @app.get("/test/protected")
    @jwt_required
    def protected():
        return jsonify(
            {
                "success": True,
                "data": {
                    "user": g.authenticated_user,
                },
            }
        ), 200

    return app


def test_jwt_required_accepts_valid_token():
    app = _create_protected_app()

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True


def test_jwt_required_accepts_bearer_case_insensitive():
    app = _create_protected_app()

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"bearer {token}",
        },
    )

    assert response.status_code == 200


def test_jwt_required_rejects_expired_token():
    app = _create_protected_app()

    expired_at = (
        datetime.now(timezone.utc)
        - timedelta(minutes=5)
    )

    payload = {
        "sub": "1",
        "email": "admin@loopandlove.com",
        "type": "access",
        "exp": expired_at,
    }

    token = jwt.encode(
        payload,
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False
    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )


def test_jwt_required_rejects_wrong_secret():
    app = _create_protected_app()

    token = jwt.encode(
        {
            "sub": "1",
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        "secret-completamente-incorrecto-123456789",
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"]["code"] == (
        "INVALID_OR_EXPIRED_TOKEN"
    )


def test_jwt_required_rejects_invalid_token_type():
    app = _create_protected_app()

    token = jwt.encode(
        {
            "sub": "1",
            "email": "admin@loopandlove.com",
            "type": "refresh",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"]["code"] == (
        "INVALID_OR_EXPIRED_TOKEN"
    )


def test_jwt_required_rejects_token_without_subject():
    app = _create_protected_app()

    token = jwt.encode(
        {
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"]["code"] == (
        "INVALID_OR_EXPIRED_TOKEN"
    )


def test_jwt_required_rejects_token_without_email():
    app = _create_protected_app()

    token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"]["code"] == (
        "INVALID_OR_EXPIRED_TOKEN"
    )

def test_jwt_required_rejects_non_numeric_subject():
    app = _create_protected_app()

    token = jwt.encode(
        {
            "sub": "abc",
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )

def test_jwt_required_rejects_inactive_admin():
    inactive_admin = AdminUserEntity(
        id=1,
        email="admin@loopandlove.com",
        password_hash="test-hash",
        is_active=False,
    )

    app = _create_protected_app(
        admin_user=inactive_admin
    )

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )


def test_jwt_required_rejects_existing_token_when_admin_no_longer_exists():
    repository = FakeAdminUserRepository(
        admin_user=None
    )

    app = _create_protected_app(
        repository=repository
    )

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )

    assert repository.get_by_id_calls == [
        1
    ]


def test_jwt_required_uses_database_user_email():
    active_admin = AdminUserEntity(
        id=1,
        email="database@loopandlove.com",
        password_hash="test-hash",
        is_active=True,
    )

    app = _create_protected_app(
        admin_user=active_admin
    )

    token = JWTService.create_access_token(
        user_id=1,
        email="token@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True

    assert data["data"]["user"] == {
        "id": 1,
        "email": "database@loopandlove.com",
    }


def test_jwt_required_returns_503_when_admin_state_cannot_be_checked():
    repository = FakeAdminUserRepository(
        error=SQLAlchemyError(
            "database unavailable"
        )
    )

    app = _create_protected_app(
        repository=repository
    )

    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 503

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_UNAVAILABLE"
    )

    response_text = response.get_data(
        as_text=True
    )

    assert (
        "database unavailable"
        not in response_text
    )

def test_jwt_required_rejects_revoked_token_version():
    active_admin = AdminUserEntity(
        id=1,
        email="admin@loopandlove.com",
        password_hash="test-hash",
        is_active=True,
        token_version=1,
    )

    app = _create_protected_app(
        admin_user=active_admin
    )

    token = (
        JWTService.create_access_token(
            user_id=1,
            email=active_admin.email,
            token_version=0,
        )
    )

    client = app.test_client()

    response = client.get(
        "/test/protected",
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )