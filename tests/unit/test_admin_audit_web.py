from types import SimpleNamespace

from app import create_app


class FakeAdminUserRepository:
    def __init__(self, users=None):
        self.users = list(users or [])

    def count(self):
        return len(self.users)

    def get_by_id(self, user_id):
        for user in self.users:
            if user.id == user_id:
                return user

        return None


def _create_web_app(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://"
            "@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    app = create_app("development")

    app.extensions["admin_user_repository"] = (
        FakeAdminUserRepository(
            users=[
                SimpleNamespace(
                    id=1,
                    name="María Gómez",
                    email="maria@example.com",
                    is_active=True,
                    token_version=0,
                )
            ]
        )
    )

    return app


def test_admin_audit_page_renders_filters_and_table(monkeypatch):
    app = _create_web_app(monkeypatch)

    response = app.test_client().get(
        "/admin/audit-logs"
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert "Registro de actividad" in body
    assert 'id="admin-audit-actor"' in body
    assert 'id="admin-audit-action"' in body
    assert 'id="admin-audit-entity-type"' in body
    assert 'id="admin-audit-date-from"' in body
    assert 'id="admin-audit-date-to"' in body
    assert 'id="admin-audit-table-body"' in body
    assert "/static/css/admin-audit.css" in body
    assert "/static/js/admin-audit.js" in body


def test_admin_navigation_includes_audit_page(monkeypatch):
    app = _create_web_app(monkeypatch)

    response = app.test_client().get(
        "/admin/audit-logs"
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert 'href="/admin/audit-logs"' in body
    assert "Auditoría" in body


def test_admin_audit_script_uses_protected_read_only_endpoint(monkeypatch):
    app = _create_web_app(monkeypatch)

    response = app.test_client().get(
        "/static/js/admin-audit.js"
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert "/api/admin/audit-logs?" in body
    assert 'method: "POST"' not in body
    assert 'method: "PATCH"' not in body
    assert 'method: "DELETE"' not in body
    assert "admin-audit-actor" in body
    assert "admin-audit-action" in body
    assert "admin-audit-entity-type" in body
    assert "admin-audit-date-from" in body
    assert "admin-audit-date-to" in body