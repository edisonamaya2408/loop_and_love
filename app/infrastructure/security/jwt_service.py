from datetime import datetime, timedelta, timezone

import jwt

from app.config.settings import Config


class JWTService:
    """Servicio para creación y validación de tokens JWT."""

    ALGORITHM = "HS256"

    @staticmethod
    def create_access_token(
        user_id: int,
        email: str,
        token_version: int = 0,
    ) -> str:
        if (
            not isinstance(user_id, int)
            or isinstance(user_id, bool)
            or user_id <= 0
        ):
            raise ValueError(
                "El usuario no es válido."
            )

        if (
            not isinstance(email, str)
            or not email.strip()
        ):
            raise ValueError(
                "El correo no es válido."
            )

        if (
            not isinstance(token_version, int)
            or isinstance(token_version, bool)
            or token_version < 0
        ):
            raise ValueError(
                "La versión del token no es válida."
            )

        now = datetime.now(
            timezone.utc
        )

        expires_at = (
            now
            + timedelta(
                minutes=(
                    Config.JWT_ACCESS_TOKEN_EXPIRES_MINUTES
                )
            )
        )

        payload = {
            "sub": str(user_id),
            "email": email,
            "iat": now,
            "exp": expires_at,
            "type": "access",
            "token_version": token_version,
        }

        return jwt.encode(
            payload,
            Config.JWT_SECRET_KEY,
            algorithm=JWTService.ALGORITHM,
        )

    @staticmethod
    def decode_access_token(
        token: str,
    ) -> dict:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET_KEY,
            algorithms=[
                JWTService.ALGORITHM
            ],
        )

        if payload.get("type") != "access":
            raise ValueError(
                "El token no es un token de acceso válido."
            )

        if "sub" not in payload:
            raise ValueError(
                "El token no contiene un usuario válido."
            )

        try:
            user_id = int(
                payload["sub"]
            )
        except (
            TypeError,
            ValueError,
        ):
            raise ValueError(
                "El token no contiene un usuario válido."
            )

        if user_id <= 0:
            raise ValueError(
                "El token no contiene un usuario válido."
            )

        if "email" not in payload:
            raise ValueError(
                "El token no contiene un correo válido."
            )

        if not isinstance(
            payload["email"],
            str,
        ):
            raise ValueError(
                "El token no contiene un correo válido."
            )

        if not payload["email"].strip():
            raise ValueError(
                "El token no contiene un correo válido."
            )

        if "token_version" not in payload:
            raise ValueError(
                "El token no contiene una versión válida."
            )

        token_version = payload[
            "token_version"
        ]

        if (
            not isinstance(
                token_version,
                int,
            )
            or isinstance(
                token_version,
                bool,
            )
            or token_version < 0
        ):
            raise ValueError(
                "El token no contiene una versión válida."
            )

        return payload