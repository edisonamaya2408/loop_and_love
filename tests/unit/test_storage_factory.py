from flask import Flask
from app.config.settings import Config
from app.infrastructure.storage.local_storage_repository import (
    LocalStorageRepository,
)
from app.infrastructure.storage.supabase_storage_repository import (
    SupabaseStorageRepository,
)
from app.infrastructure.storage.storage_factory import (
    create_storage_repository,
)

def test_auto_uses_supabase_from_flask_production_environment(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        "test-key",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_STORAGE_BUCKET",
        "products",
    )

    class FakeStorage:
        def from_(self, bucket):
            return self

    class FakeClient:
        storage = FakeStorage()

    monkeypatch.setattr(
        "app.infrastructure.storage.supabase_storage_repository.create_client",
        lambda url, key: FakeClient(),
    )

    app = Flask(
        __name__
    )

    app.config.update(
        ENVIRONMENT="production",
        STORAGE_PROVIDER="auto",
    )

    with app.app_context():
        repository = create_storage_repository()

    assert isinstance(
        repository,
        SupabaseStorageRepository,
    )


def test_production_rejects_local_storage_from_factory():
    app = Flask(
        __name__
    )

    app.config.update(
        ENVIRONMENT="production",
        STORAGE_PROVIDER="local",
    )

    with app.app_context():
        try:
            create_storage_repository()

            assert False, (
                "Se esperaba RuntimeError"
            )

        except RuntimeError as error:
            assert (
                "El almacenamiento local no está "
                "permitido en producción"
                in str(error)
            )

def test_auto_uses_local_storage_in_development(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "auto",
    )

    monkeypatch.setattr(
        Config,
        "ENVIRONMENT",
        "development",
    )

    repository = create_storage_repository()

    assert isinstance(
        repository,
        LocalStorageRepository,
    )


def test_auto_uses_supabase_storage_in_production(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "auto",
    )

    monkeypatch.setattr(
        Config,
        "ENVIRONMENT",
        "production",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        "test-key",
    )

    class FakeStorage:
        def from_(self, bucket):
            return self

    class FakeClient:
        storage = FakeStorage()

    def fake_create_client(url, key):
        return FakeClient()

    monkeypatch.setattr(
        "app.infrastructure.storage.supabase_storage_repository.create_client",
        fake_create_client,
    )

    repository = create_storage_repository()

    assert isinstance(
        repository,
        SupabaseStorageRepository,
    )


def test_explicit_local_provider_uses_local_storage(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "local",
    )

    monkeypatch.setenv(
        "FLASK_ENV",
        "production",
    )

    repository = create_storage_repository()

    assert isinstance(
        repository,
        LocalStorageRepository,
    )


def test_explicit_supabase_provider_uses_supabase_storage(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "supabase",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        Config,
        "SUPABASE_KEY",
        "test-key",
    )

    class FakeStorage:
        def from_(self, bucket):
            return self

    class FakeClient:
        storage = FakeStorage()

    def fake_create_client(url, key):
        return FakeClient()

    monkeypatch.setattr(
        "app.infrastructure.storage.supabase_storage_repository.create_client",
        fake_create_client,
    )

    repository = create_storage_repository()

    assert isinstance(
        repository,
        SupabaseStorageRepository,
    )


def test_invalid_provider_raises_error(
    monkeypatch,
):
    monkeypatch.setattr(
        Config,
        "STORAGE_PROVIDER",
        "invalid",
    )

    try:
        create_storage_repository()
        assert False, "Se esperaba RuntimeError"
    except RuntimeError as error:
        assert (
            "STORAGE_PROVIDER no válido"
            in str(error)
        )