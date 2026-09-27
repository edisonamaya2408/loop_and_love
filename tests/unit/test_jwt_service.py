import jwt
import pytest

from app.config.settings import Config
from app.infrastructure.security.jwt_service import JWTService


def test_create_and_decode_access_token():
    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
    )

    payload = JWTService.decode_access_token(
        token
    )

    assert payload["sub"] == "1"
    assert payload["email"] == "admin@loopandlove.com"
    assert payload["type"] == "access"
    assert payload["token_version"] == 0


def test_decode_rejects_invalid_token():
    with pytest.raises(jwt.InvalidTokenError):
        JWTService.decode_access_token(
            "token-invalido"
        )

def test_decode_rejects_non_numeric_subject():
    token = jwt.encode(
        {
            "sub": "abc",
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    with pytest.raises(ValueError):
        JWTService.decode_access_token(token)


def test_decode_rejects_non_positive_subject():
    token = jwt.encode(
        {
            "sub": "0",
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    with pytest.raises(ValueError):
        JWTService.decode_access_token(token)

def test_create_and_decode_access_token_with_token_version():
    token = JWTService.create_access_token(
        user_id=1,
        email="admin@loopandlove.com",
        token_version=7,
    )

    payload = JWTService.decode_access_token(
        token
    )

    assert payload["token_version"] == 7


def test_decode_rejects_token_without_token_version():
    token = jwt.encode(
        {
            "sub": "1",
            "email": "admin@loopandlove.com",
            "type": "access",
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    with pytest.raises(
        ValueError,
        match="versión válida",
    ):
        JWTService.decode_access_token(
            token
        )


def test_decode_rejects_negative_token_version():
    token = jwt.encode(
        {
            "sub": "1",
            "email": "admin@loopandlove.com",
            "type": "access",
            "token_version": -1,
        },
        Config.JWT_SECRET_KEY,
        algorithm=JWTService.ALGORITHM,
    )

    with pytest.raises(
        ValueError,
        match="versión válida",
    ):
        JWTService.decode_access_token(
            token
        )