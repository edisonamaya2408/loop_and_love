from types import SimpleNamespace

import pytest

from tests.unit.audit_test_helpers import (
    InMemoryAdminAuditRepository,
)

from app import create_app


class FakeCategoryService:
    def __init__(self):
        self.categories = {
            1: SimpleNamespace(
                id=1,
                name="Amigurumis",
                slug="amigurumis",
                is_active=True,
                created_at=None,
                updated_at=None,
            ),
            2: SimpleNamespace(
                id=2,
                name="Decoración",
                slug="decoracion",
                is_active=False,
                created_at=None,
                updated_at=None,
            ),
        }

    def list_all_categories(self):
        return list(
            self.categories.values()
        )

    def get_category(
        self,
        category_id,
    ):
        return self.categories.get(
            category_id
        )

    def create_category(
        self,
        name,
        is_active=True,
    ):
        return SimpleNamespace(
            id=3,
            name=name,
            slug="nueva-categoria",
            is_active=is_active,
            created_at=None,
            updated_at=None,
        )

    def update_category(
        self,
        category_id,
        name,
        is_active,
    ):
        return SimpleNamespace(
            id=category_id,
            name=name,
            slug="categoria-actualizada",
            is_active=is_active,
            created_at=None,
            updated_at=None,
        )

    def delete_category(
        self,
        category_id,
    ):
        category = self.categories.get(
            category_id
        )

        if category is None:
            raise LookupError(
                "La categoría no existe."
            )

        if category_id == 2:
            raise ValueError(
                "No se puede eliminar la categoría porque "
                "tiene productos asociados. "
                "Desactívela en lugar de eliminarla."
            )

        return category

class FakeAdminUserRepository:
    def __init__(self):
        self.admin_user = SimpleNamespace(
            id=1,
            name="Administrador de prueba",
            email="admin@test.com",
            is_active=True,
            token_version=0,
        )

    def get_by_id(
        self,
        user_id,
    ):
        if user_id != self.admin_user.id:
            return None

        return self.admin_user


def _auth_headers():
    return {
        "Authorization": "Bearer test-token",
    }


def _configure_valid_jwt(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.security.jwt_service.JWTService.decode_access_token",
        lambda token: {
            "sub": "1",
            "email": "admin@test.com",
            "token_version": 0,
        },
    )


def _configure_invalid_jwt(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.security.jwt_service.JWTService.decode_access_token",
        lambda token: (_ for _ in ()).throw(
            ValueError("invalid token")
        ),
    )


def _create_test_app(monkeypatch):
    app = create_app(
        "development"
    )

    app.extensions[
        "admin_audit_repository"
    ] = InMemoryAdminAuditRepository()

    category_service = FakeCategoryService()

    admin_user_repository = (
        FakeAdminUserRepository()
    )

    app.extensions[
        "admin_user_repository"
    ] = admin_user_repository

    monkeypatch.setattr(
        "app.presentation.routes.admin_category_routes._get_category_service",
        lambda: category_service,
    )

    return app, category_service


def test_list_admin_categories_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/categories"
    )

    assert response.status_code == 401


def test_list_admin_categories_returns_all_categories(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/categories",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert len(payload["data"]) == 2

    names = [
        category["name"]
        for category in payload["data"]
    ]

    assert "Amigurumis" in names
    assert "Decoración" in names


def test_get_admin_category_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/categories/1"
    )

    assert response.status_code == 401


def test_get_admin_category_returns_inactive_category(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/categories/2",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["data"]["id"] == 2
    assert payload["data"]["name"] == "Decoración"
    assert payload["data"]["is_active"] is False


def test_get_admin_category_returns_404_when_not_found(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/admin/categories/999",
        headers=_auth_headers(),
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "CATEGORY_NOT_FOUND"
    )


def test_create_admin_category_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/categories",
        json={
            "name": "Nueva categoría",
            "is_active": True,
        },
    )

    assert response.status_code == 401


def test_create_admin_category_returns_201(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/categories",
        json={
            "name": "Nueva categoría",
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 201

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["data"]["id"] == 3
    assert (
        payload["data"]["name"]
        == "Nueva categoría"
    )
    assert (
        payload["data"]["slug"]
        == "nueva-categoria"
    )
    assert payload["data"]["is_active"] is True


def test_create_admin_category_without_json_returns_400(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.post(
        "/api/admin/categories",
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "INVALID_REQUEST"
    )


def test_update_admin_category_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/categories/1",
        json={
            "name": "Amigurumis premium",
            "is_active": True,
        },
    )

    assert response.status_code == 401


def test_update_admin_category_returns_200(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/categories/1",
        json={
            "name": "Amigurumis premium",
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["data"]["id"] == 1
    assert (
        payload["data"]["name"]
        == "Amigurumis premium"
    )
    assert (
        payload["data"]["slug"]
        == "categoria-actualizada"
    )
    assert payload["data"]["is_active"] is True


def test_update_admin_category_requires_name(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/categories/1",
        json={
            "is_active": True,
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "INVALID_REQUEST"
    )


def test_update_admin_category_requires_is_active(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/categories/1",
        json={
            "name": "Amigurumis premium",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "INVALID_REQUEST"
    )


def test_update_admin_category_rejects_invalid_is_active(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.put(
        "/api/admin/categories/1",
        json={
            "name": "Amigurumis premium",
            "is_active": "true",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "INVALID_REQUEST"
    )


def test_delete_admin_category_requires_authentication(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/categories/1"
    )

    assert response.status_code == 401


def test_delete_admin_category_returns_200(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/categories/1",
        headers=_auth_headers(),
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["data"]["id"] == 1


def test_delete_admin_category_with_products_returns_400(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_valid_jwt(
        monkeypatch
    )

    client = app.test_client()

    response = client.delete(
        "/api/admin/categories/2",
        headers=_auth_headers(),
    )

    assert response.status_code == 400

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "VALIDATION_ERROR"
    )


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/admin/categories"),
        ("get", "/api/admin/categories/1"),
        ("post", "/api/admin/categories"),
        ("put", "/api/admin/categories/1"),
        ("delete", "/api/admin/categories/1"),
    ],
)
def test_admin_category_endpoints_reject_invalid_token(
    monkeypatch,
    method,
    path,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    _configure_invalid_jwt(
        monkeypatch
    )

    client = app.test_client()

    request_method = getattr(
        client,
        method,
    )

    kwargs = {
        "headers": _auth_headers(),
    }

    if method in {"post", "put"}:
        kwargs["json"] = {
            "name": "Amigurumis",
            "is_active": True,
        }

    response = request_method(
        path,
        **kwargs,
    )

    assert response.status_code == 401