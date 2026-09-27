import pytest

from app import create_app


class FakeCategoryService:
    def __init__(self):
        from types import SimpleNamespace

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

    def list_active_categories(self):
        return [
            category
            for category in self.categories.values()
            if category.is_active
        ]

    def get_category(
        self,
        category_id,
    ):
        return self.categories.get(
            category_id
        )


def _create_test_app(monkeypatch):
    app = create_app(
        "development"
    )

    service = FakeCategoryService()

    monkeypatch.setattr(
        "app.presentation.routes.category_routes._get_category_service",
        lambda: service,
    )

    return app, service


def test_list_categories_returns_active_categories(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/categories"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert len(payload["data"]) == 1

    category = payload["data"][0]

    assert category["id"] == 1
    assert category["name"] == "Amigurumis"
    assert category["slug"] == "amigurumis"
    assert category["is_active"] is True


def test_list_categories_does_not_return_inactive_categories(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/categories"
    )

    assert response.status_code == 200

    payload = response.get_json()

    category_ids = [
        category["id"]
        for category in payload["data"]
    ]

    assert 2 not in category_ids


def test_get_category_returns_active_category(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/categories/1"
    )

    assert response.status_code == 200

    payload = response.get_json()

    assert payload["success"] is True
    assert payload["data"]["id"] == 1
    assert payload["data"]["name"] == "Amigurumis"
    assert payload["data"]["slug"] == "amigurumis"
    assert payload["data"]["is_active"] is True


def test_get_category_does_not_expose_inactive_category(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/categories/2"
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "CATEGORY_NOT_FOUND"
    )


def test_get_category_returns_404_when_not_found(
    monkeypatch,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        "/api/categories/999"
    )

    assert response.status_code == 404

    payload = response.get_json()

    assert payload["success"] is False
    assert (
        payload["error"]["code"]
        == "CATEGORY_NOT_FOUND"
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/categories/0",
        "/api/categories/-1",
    ],
)
def test_get_category_invalid_path_returns_not_found(
    monkeypatch,
    path,
):
    app, _ = _create_test_app(
        monkeypatch
    )

    client = app.test_client()

    response = client.get(
        path
    )

    assert response.status_code == 404