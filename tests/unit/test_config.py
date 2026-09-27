import pytest

from app import create_app
from app.config.settings import (
    get_database_url,
    normalize_database_url,
    ProductionConfig,
)

@pytest.fixture(autouse=True)
def valid_production_storage_configuration(
    monkeypatch,
):
    """
    Mantiene una configuración de Storage válida para
    las pruebas de producción, salvo cuando una prueba
    cambia explícitamente ese valor.
    """

    monkeypatch.setattr(
        ProductionConfig,
        "STORAGE_PROVIDER",
        "auto",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_URL",
        "https://example.supabase.co",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_KEY",
        "test-secret-key",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_STORAGE_BUCKET",
        "products",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "redis://localhost:6379/0",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "TRUSTED_PROXY_COUNT",
        1,
    )


def test_create_app_uses_development_environment():
    app = create_app("development")

    assert app.config["ENVIRONMENT"] == "development"
    assert app.config["DEBUG"] is True


def test_create_app_uses_production_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "b" * 64,
    )

    app = create_app("production")

    assert app.config[
        "ENVIRONMENT"
    ] == "production"

    assert app.config[
        "DEBUG"
    ] is False


def test_create_app_rejects_invalid_environment():
    with pytest.raises(
        RuntimeError,
        match="APP_ENV no válido",
    ):
        create_app("invalid")

def test_development_rejects_short_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.JWT_SECRET_KEY",
        "short",
    )

    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET_KEY debe tener al menos 32 bytes",
    ):
        create_app("development")

def test_production_rejects_default_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "dev-jwt-secret-key",
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "JWT_SECRET_KEY no puede utilizar "
            "un valor predeterminado o de ejemplo "
            "en producción"
        ),
    ):
        create_app("production")

def test_production_accepts_valid_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    app = create_app("production")

    assert app.config[
        "ENVIRONMENT"
    ] == "production"

def test_normalize_postgresql_url_uses_psycopg():
    assert (
        normalize_database_url(
            "postgresql://user:password@host:5432/db"
        )
        == (
            "postgresql+psycopg://"
            "user:password@host:5432/db"
        )
    )


def test_normalize_legacy_postgres_url_uses_psycopg():
    assert (
        normalize_database_url(
            "postgres://user:password@host:5432/db"
        )
        == (
            "postgresql+psycopg://"
            "user:password@host:5432/db"
        )
    )


def test_normalize_psycopg_url_does_not_change_it():
    url = (
        "postgresql+psycopg://"
        "user:password@host:5432/db"
    )

    assert normalize_database_url(url) == url


def test_normalize_sql_server_url_does_not_change_it():
    url = (
        "mssql+pyodbc://@SERVER/loop_and_love"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    assert normalize_database_url(url) == url


def test_normalize_empty_database_url():
    assert normalize_database_url(None) is None
    assert normalize_database_url("") == ""


def test_normalize_database_url_preserves_query_parameters():
    url = (
        "postgresql://"
        "user:password@host:5432/db"
        "?sslmode=require"
    )

    assert (
        normalize_database_url(url)
        == (
            "postgresql+psycopg://"
            "user:password@host:5432/db"
            "?sslmode=require"
        )
    )

def test_testing_environment_uses_test_database(
    monkeypatch,
):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/testdb"
        ),
    )

    assert (
        get_database_url("testing")
        == (
            "postgresql+psycopg://"
            "user:password@host:5432/testdb"
        )
    )


def test_development_environment_uses_database_url(
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

    assert get_database_url(
        "development"
    ).startswith(
        "mssql+pyodbc://"
    )


def test_create_app_uses_testing_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/testdb"
        ),
    )

    app = create_app(
        "testing"
    )

    assert app.config[
        "ENVIRONMENT"
    ] == "testing"

    assert app.config[
        "TESTING"
    ] is True

    assert app.config[
        "SQLALCHEMY_DATABASE_URI"
    ].startswith(
        "postgresql+psycopg://"
    )


def test_testing_environment_requires_test_database(
    monkeypatch,
):
    monkeypatch.delenv(
        "TEST_DATABASE_URL",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="TEST_DATABASE_URL es obligatorio",
    ):
        create_app("testing")

def test_invalid_database_driver_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@host:3306/db",
    )

    with pytest.raises(
        RuntimeError,
        match="Drivers permitidos",
    ):
        create_app("development")


def test_invalid_cors_origin_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.CORS_ORIGINS",
        "ftp://example.com",
    )

    with pytest.raises(
        RuntimeError,
        match="CORS_ORIGINS no válido",
    ):
        create_app("development")


def test_multiple_cors_origins_are_accepted(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.CORS_ORIGINS",
        (
            "http://localhost:5000, "
            "https://example.com/"
        ),
    )

    app = create_app(
        "development"
    )

    assert app.config[
        "CORS_ORIGINS_LIST"
    ] == [
        "http://localhost:5000",
        "https://example.com",
    ]


def test_invalid_storage_provider_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.STORAGE_PROVIDER",
        "invalid",
    )

    with pytest.raises(
        RuntimeError,
        match="STORAGE_PROVIDER no válido",
    ):
        create_app(
            "development"
        )


def test_non_positive_jwt_expiration_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig."
        "JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "JWT_ACCESS_TOKEN_EXPIRES_MINUTES "
            "no válido"
        ),
    ):
        create_app(
            "development"
        )


def test_non_positive_image_size_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig."
        "MAX_IMAGE_SIZE_MB",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match="MAX_IMAGE_SIZE_MB no válido",
    ):
        create_app(
            "development"
        )

def test_production_requires_secret_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "",
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY no puede estar vacío",
    ):
        create_app("production")


def test_production_requires_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "",
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match="JWT_SECRET_KEY no puede estar vacío",
    ):
        create_app("production")


def test_production_rejects_short_secret_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 31,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY debe tener al menos 32 bytes",
    ):
        create_app("production")


def test_production_rejects_example_secret_key(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "change-this-secret-key",
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "SECRET_KEY no puede utilizar "
            "un valor predeterminado o de ejemplo"
        ),
    ):
        create_app("production")


def test_production_rejects_example_jwt_secret(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        "app.config.settings.ProductionConfig.JWT_SECRET_KEY",
        "generate-a-secure-random-secret-at-least-32-bytes",
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:password@host:5432/db?sslmode=require",
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "JWT_SECRET_KEY no puede utilizar "
            "un valor predeterminado o de ejemplo"
        ),
    ):
        create_app("production")


def test_development_allows_development_secret_defaults(
    monkeypatch,
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "mssql+pyodbc://@SERVER/loop_and_love"
            "?driver=ODBC+Driver+17+for+SQL+Server"
        ),
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.SECRET_KEY",
        "dev-secret-key",
    )

    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.JWT_SECRET_KEY",
        "a" * 64,
    )

    app = create_app(
        "development"
    )

    assert app.config[
        "ENVIRONMENT"
    ] == "development"

def test_sqlalchemy_pool_configuration():
    app = create_app(
        "development"
    )

    options = app.config[
        "SQLALCHEMY_ENGINE_OPTIONS"
    ]

    assert options[
        "pool_pre_ping"
    ] is True

    assert options[
        "pool_size"
    ] == 3

    assert options[
        "max_overflow"
    ] == 2

    assert options[
        "pool_timeout"
    ] == 10

    assert options[
        "pool_recycle"
    ] == 1800


def test_testing_uses_restricted_sqlalchemy_pool(
    monkeypatch,
):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/testdb"
        ),
    )

    app = create_app(
        "testing"
    )

    options = app.config[
        "SQLALCHEMY_ENGINE_OPTIONS"
    ]

    assert options[
        "pool_pre_ping"
    ] is True

    assert options[
        "pool_size"
    ] == 2

    assert options[
        "max_overflow"
    ] == 0

    assert options[
        "pool_timeout"
    ] == 10

    assert options[
        "pool_recycle"
    ] == 1800


def test_invalid_pool_size_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.SQLALCHEMY_POOL_SIZE",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match="SQLALCHEMY_POOL_SIZE no válido",
    ):
        create_app(
            "development"
        )


def test_negative_pool_overflow_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.SQLALCHEMY_MAX_OVERFLOW",
        -1,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "SQLALCHEMY_MAX_OVERFLOW no válido"
        ),
    ):
        create_app(
            "development"
        )


def test_invalid_pool_timeout_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.SQLALCHEMY_POOL_TIMEOUT",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match="SQLALCHEMY_POOL_TIMEOUT no válido",
    ):
        create_app(
            "development"
        )


def test_invalid_pool_recycle_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig.SQLALCHEMY_POOL_RECYCLE",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match="SQLALCHEMY_POOL_RECYCLE no válido",
    ):
        create_app(
            "development"
        )

def test_max_content_length_is_based_on_image_limit():
    app = create_app(
        "development"
    )

    expected = (
        5 + 1
    ) * 1024 * 1024

    assert app.config[
        "MAX_CONTENT_LENGTH"
    ] == expected

    assert app.config[
        "MAX_UPLOAD_REQUEST_OVERHEAD_MB"
    ] == 1

def test_invalid_upload_request_overhead_is_rejected(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.config.settings.DevelopmentConfig."
        "MAX_UPLOAD_REQUEST_OVERHEAD_MB",
        0,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "MAX_UPLOAD_REQUEST_OVERHEAD_MB "
            "no válido"
        ),
    ):
        create_app(
            "development"
        )

def test_production_requires_supabase_url(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_URL",
        "",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_URL no válido",
    ):
        create_app("production")


def test_production_requires_supabase_key(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_KEY",
        "",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="SUPABASE_KEY no puede estar vacío",
    ):
        create_app("production")


def test_production_rejects_insecure_supabase_url(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "SUPABASE_URL",
        "http://example.supabase.co",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "SUPABASE_URL no válido.*"
            "En producción debe utilizar https"
        ),
    ):
        create_app("production")


def test_production_rejects_local_storage(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "STORAGE_PROVIDER",
        "local",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "El almacenamiento local no está "
            "permitido en producción"
        ),
    ):
        create_app("production")

def test_production_rejects_memory_rate_limit_storage(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "El almacenamiento en memoria "
            "no está permitido en producción"
        ),
    ):
        create_app(
            "production"
        )


def test_production_accepts_redis_rate_limit_storage(
    monkeypatch,
):
    monkeypatch.setattr(
        ProductionConfig,
        "RATELIMIT_STORAGE_URI",
        "redis://localhost:6379/0",
    )

    monkeypatch.setattr(
        ProductionConfig,
        "SECRET_KEY",
        "a" * 64,
    )

    monkeypatch.setattr(
        ProductionConfig,
        "JWT_SECRET_KEY",
        "b" * 64,
    )

    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://"
            "user:password@host:5432/db"
            "?sslmode=require"
        ),
    )

    app = create_app(
        "production"
    )

    assert (
        app.config[
            "RATELIMIT_STORAGE_URI"
        ]
        == "redis://localhost:6379/0"
    )


def test_rate_limit_strategy_accepts_supported_value():
    from app.config.settings import (
        validate_rate_limit_strategy,
    )

    assert (
        validate_rate_limit_strategy(
            "sliding-window-counter"
        )
        == "sliding-window-counter"
    )


def test_rate_limit_strategy_rejects_invalid_value():
    from app.config.settings import (
        validate_rate_limit_strategy,
    )

    with pytest.raises(
        RuntimeError,
        match="RATELIMIT_STRATEGY no válido",
    ):
        validate_rate_limit_strategy(
            "invalid-strategy"
        )