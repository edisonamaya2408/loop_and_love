import json
from pathlib import Path

from app import create_app


OPENAPI_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "openapi.json"
)


EXPECTED_OPERATIONS = {
    ("GET", "/health"),
    ("GET", "/health/db"),
    ("GET", "/health/storage"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/auth/logout"),
    ("GET", "/api/products"),
    ("GET", "/api/products/<int:product_id>"),
    ("GET", "/api/categories"),
    ("GET", "/api/categories/<int:category_id>"),
    ("GET", "/api/admin/products"),
    ("POST", "/api/admin/products"),
    ("GET", "/api/admin/products/<int:product_id>"),
    ("PUT", "/api/admin/products/<int:product_id>"),
    (
        "PATCH",
        "/api/admin/products/<int:product_id>/status",
    ),
    (
        "DELETE",
        "/api/admin/products/<int:product_id>",
    ),
    (
        "DELETE",
        "/api/admin/products/<int:product_id>/image",
    ),
    ("GET", "/api/admin/categories"),
    ("POST", "/api/admin/categories"),
    (
        "GET",
        "/api/admin/categories/<int:category_id>",
    ),
    (
        "PUT",
        "/api/admin/categories/<int:category_id>",
    ),
    (
        "DELETE",
        "/api/admin/categories/<int:category_id>",
    ),
    ("GET", "/api/admin/users"),
    ("POST", "/api/admin/users"),
    ("GET", "/api/admin/users/<int:user_id>"),
    ("PATCH", "/api/admin/users/<int:user_id>"),
    ("POST", "/api/orders"),
}


EXPECTED_OPENAPI_PATHS = {
    "/health",
    "/health/db",
    "/health/storage",
    "/api/auth/login",
    "/api/auth/logout",
    "/api/products",
    "/api/products/{product_id}",
    "/api/categories",
    "/api/categories/{category_id}",
    "/api/admin/products",
    "/api/admin/products/{product_id}",
    "/api/admin/products/{product_id}/image",
    "/api/admin/products/{product_id}/status",
    "/api/admin/categories",
    "/api/admin/categories/{category_id}",
    "/api/admin/users",
    "/api/admin/users/{user_id}",
    "/api/orders",
}


def _load_openapi():
    with OPENAPI_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def _is_documented_api_route(rule):
    return (
        rule.rule.startswith("/api/")
        or rule.rule.startswith("/health")
    )


def test_openapi_document_is_valid_json_with_required_metadata():
    document = _load_openapi()

    assert document["openapi"] == "3.0.3"

    assert (
        document["info"]["title"]
        == "Loop & Love API"
    )

    assert (
        document["info"]["version"]
        == "1.0.0"
    )

    assert document["paths"]

    assert "components" in document

    assert (
        "securitySchemes"
        in document["components"]
    )

    assert (
        "bearerAuth"
        in document["components"][
            "securitySchemes"
        ]
    )


def test_openapi_documents_every_current_explicit_api_route(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app(
        "development"
    )

    explicit_operations = {
        (method, rule.rule)
        for rule in app.url_map.iter_rules()
        if _is_documented_api_route(rule)
        for method in rule.methods
        if method in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }
    }

    assert (
        explicit_operations
        == EXPECTED_OPERATIONS
    )

    document = _load_openapi()

    openapi_operations = {
        (
            method.upper(),
            path,
        )
        for path, item in document["paths"].items()
        for method in item
        if method in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
    }

    path_translation = {
        (
            method,
            path.replace(
                "{product_id}",
                "<int:product_id>",
            ).replace(
                "{category_id}",
                "<int:category_id>",
            ).replace(
                "{user_id}",
                "<int:user_id>",
            ),
        )
        for method, path in openapi_operations
    }

    assert (
        path_translation
        == EXPECTED_OPERATIONS
    )

    assert (
        set(document["paths"])
        == EXPECTED_OPENAPI_PATHS
    )


def test_openapi_operation_ids_are_unique():
    document = _load_openapi()

    operation_ids = [
        operation["operationId"]
        for path_item in document[
            "paths"
        ].values()
        for method, operation in path_item.items()
        if method in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
    ]

    assert (
        len(operation_ids)
        == len(set(operation_ids))
    )


def test_openapi_protected_routes_use_bearer_auth():
    document = _load_openapi()

    protected_paths = {
        "/health/db",
        "/health/storage",
        "/api/auth/logout",
        "/api/admin/products",
        "/api/admin/products/{product_id}",
        "/api/admin/products/{product_id}/image",
        "/api/admin/products/{product_id}/status",
        "/api/admin/categories",
        "/api/admin/categories/{category_id}",
        "/api/admin/users",
        "/api/admin/users/{user_id}",
    }

    for path in protected_paths:
        for operation in (
            document["paths"][path].values()
        ):
            assert operation[
                "security"
            ] == [
                {"bearerAuth": []}
            ]


def test_openapi_public_catalog_routes_do_not_require_authentication():
    document = _load_openapi()

    public_paths = {
        "/health",
        "/api/auth/login",
        "/api/products",
        "/api/products/{product_id}",
        "/api/categories",
        "/api/categories/{category_id}",
        "/api/orders",
    }

    for path in public_paths:
        for operation in (
            document["paths"][path].values()
        ):
            assert "security" not in operation
