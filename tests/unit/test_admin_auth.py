def test_admin_products_requires_authentication(client):
    response = client.get(
        "/api/admin/products"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "AUTHENTICATION_REQUIRED"
    )


def test_admin_products_rejects_invalid_token(client):
    response = client.get(
        "/api/admin/products",
        headers={
            "Authorization": (
                "Bearer token-completamente-invalido"
            )
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_OR_EXPIRED_TOKEN"
    )


def test_admin_products_rejects_invalid_auth_header(client):
    response = client.get(
        "/api/admin/products",
        headers={
            "Authorization": "token-invalido"
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["success"] is False

    assert (
        data["error"]["code"]
        == "INVALID_AUTHORIZATION_HEADER"
    )