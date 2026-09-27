import hashlib

from flask import request
from flask_limiter.util import get_remote_address

from app.domain.normalization import (
    normalize_email,
)


def get_login_account_identifier() -> str:
    """
    Genera un identificador estable y no reversible para
    aplicar el límite de login por cuenta.

    No almacena el correo en bruto como parte de la clave
    del rate limiter.
    """

    data = request.get_json(
        silent=True
    )

    if not isinstance(
        data,
        dict,
    ):
        return (
            "invalid:"
            + get_remote_address()
        )

    email = data.get(
        "email",
        "",
    )

    if not isinstance(
        email,
        str,
    ):
        email = ""

    normalized_email = normalize_email(
        email
    )

    if not normalized_email:
        return (
            "invalid:"
            + get_remote_address()
        )

    digest = hashlib.sha256(
        normalized_email.encode(
            "utf-8"
        )
    ).hexdigest()

    return (
        "account:"
        + digest
    )