import os

from dotenv import load_dotenv

load_dotenv()

from urllib.parse import urlparse


ALLOWED_DATABASE_DRIVERS = {
    "mssql+pyodbc",
    "postgresql+psycopg",
}

ALLOWED_STORAGE_PROVIDERS = {
    "auto",
    "local",
    "supabase",
}

ALLOWED_LOG_LEVELS = {
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
}

ALLOWED_RATE_LIMIT_STRATEGIES = {
    "fixed-window",
    "moving-window",
    "sliding-window-counter",
}

ALLOWED_RATE_LIMIT_STORAGE_SCHEMES = {
    "memory",
    "redis",
    "rediss",
}


def normalize_database_url(
    value: str | None,
) -> str | None:
    """
    Normaliza las URLs de PostgreSQL para utilizar Psycopg 3.

    Soporta:
        postgres://
        postgresql://
        postgresql+psycopg://
        mssql+pyodbc://
    """

    if not value:
        return value

    value = value.strip()

    if value.startswith("postgres://"):
        return (
            "postgresql+psycopg://"
            + value[len("postgres://"):]
        )

    if value.startswith("postgresql://"):
        return (
            "postgresql+psycopg://"
            + value[len("postgresql://"):]
        )

    return value


def get_database_url(
    environment: str,
) -> str | None:
    """
    Obtiene la URL de base de datos correspondiente
    al entorno solicitado.
    """

    if environment == "testing":
        return normalize_database_url(
            os.getenv("TEST_DATABASE_URL")
        )

    return normalize_database_url(
        os.getenv("DATABASE_URL")
    )

def validate_database_url(
    database_url: str | None,
) -> str:
    """Valida que la URL de base de datos utilice un driver soportado."""

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL es obligatorio."
        )

    normalized_url = normalize_database_url(
        database_url
    )

    parsed_url = urlparse(
        normalized_url
    )

    driver = parsed_url.scheme.lower()

    if driver not in ALLOWED_DATABASE_DRIVERS:
        allowed = ", ".join(
            sorted(ALLOWED_DATABASE_DRIVERS)
        )

        raise RuntimeError(
            "DATABASE_URL no válido. "
            f"Drivers permitidos: {allowed}."
        )

    if not parsed_url.hostname:
        raise RuntimeError(
            "DATABASE_URL no válido. "
            "Debe contener un host de base de datos."
        )

    if (
        not parsed_url.path
        or parsed_url.path == "/"
    ):
        raise RuntimeError(
            "DATABASE_URL no válido. "
            "Debe especificar la base de datos."
        )

    return normalized_url


def parse_cors_origins(
    value: str | None,
) -> list[str]:
    """Convierte y valida CORS_ORIGINS en una lista de origins."""

    if not isinstance(value, str):
        raise RuntimeError(
            "CORS_ORIGINS no válido. "
            "Debe contener al menos un origen permitido."
        )

    origins = [
        origin.strip().rstrip("/")
        for origin in value.split(",")
        if origin.strip()
    ]

    if not origins:
        raise RuntimeError(
            "CORS_ORIGINS no válido. "
            "Debe contener al menos un origen permitido."
        )

    if "*" in origins and len(origins) > 1:
        raise RuntimeError(
            "CORS_ORIGINS no válido. "
            "El origen '*' no puede combinarse "
            "con otros orígenes."
        )

    for origin in origins:
        if origin == "*":
            continue

        parsed_origin = urlparse(
            origin
        )

        if parsed_origin.scheme not in {
            "http",
            "https",
        }:
            raise RuntimeError(
                "CORS_ORIGINS no válido. "
                "Cada origen debe utilizar http o https."
            )

        if not parsed_origin.hostname:
            raise RuntimeError(
                "CORS_ORIGINS no válido. "
                "Cada origen debe contener un host válido."
            )

        if (
            parsed_origin.path not in {"", "/"}
            or parsed_origin.params
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise RuntimeError(
                "CORS_ORIGINS no válido. "
                "Los orígenes no deben contener rutas, "
                "parámetros, query string ni fragmentos."
            )

    return origins


def validate_positive_integer(
    value: object,
    setting_name: str,
) -> int:
    """Valida y devuelve un entero estrictamente positivo."""

    try:
        parsed_value = int(value)

    except (
        TypeError,
        ValueError,
    ) as error:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe ser un número entero positivo."
        ) from error

    if parsed_value <= 0:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe ser un número entero positivo."
        )

    return parsed_value

def validate_non_negative_integer(
    value: object,
    setting_name: str,
) -> int:
    """Valida y devuelve un entero mayor o igual a cero."""

    try:
        parsed_value = int(value)

    except (
        TypeError,
        ValueError,
    ) as error:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe ser un número entero mayor o igual a cero."
        ) from error

    if parsed_value < 0:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe ser un número entero mayor o igual a cero."
        )

    return parsed_value

def validate_log_level(
    value: object,
    setting_name: str = "LOG_LEVEL",
) -> str:
    """Valida un nivel de logging soportado por Python."""

    if not isinstance(value, str):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Valores permitidos: "
            f"{', '.join(sorted(ALLOWED_LOG_LEVELS))}."
        )

    normalized_value = value.strip().upper()

    if normalized_value not in ALLOWED_LOG_LEVELS:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Valores permitidos: "
            f"{', '.join(sorted(ALLOWED_LOG_LEVELS))}."
        )

    return normalized_value

def validate_rate_limit_strategy(
    value: object,
    setting_name: str = "RATELIMIT_STRATEGY",
) -> str:
    """Valida la estrategia de rate limiting."""

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            f"{setting_name} no válido."
        )

    normalized_value = (
        value.strip().lower()
    )

    if (
        normalized_value
        not in ALLOWED_RATE_LIMIT_STRATEGIES
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Valores permitidos: "
            f"{', '.join(sorted(ALLOWED_RATE_LIMIT_STRATEGIES))}."
        )

    return normalized_value


def validate_rate_limit_storage_uri(
    value: object,
    environment: str,
    setting_name: str = "RATELIMIT_STORAGE_URI",
) -> str:
    """
    Valida el almacenamiento utilizado por Flask-Limiter.

    memory://:
        permitido en development/testing.

    redis:// / rediss://:
        requeridos en production.
    """

    if not isinstance(
        value,
        str,
    ):
        raise RuntimeError(
            f"{setting_name} no válido."
        )

    normalized_value = (
        value.strip()
    )

    if not normalized_value:
        raise RuntimeError(
            f"{setting_name} no válido."
        )

    parsed_url = urlparse(
        normalized_value
    )

    scheme = (
        parsed_url.scheme
        or ""
    ).lower()

    if (
        scheme
        not in ALLOWED_RATE_LIMIT_STORAGE_SCHEMES
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe utilizar memory://, redis:// o rediss://."
        )

    if (
        environment == "production"
        and scheme == "memory"
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "El almacenamiento en memoria no está permitido "
            "en producción."
        )

    if scheme in {
        "redis",
        "rediss",
    } and not parsed_url.hostname:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "La URL Redis debe contener un host."
        )

    if (
        scheme == "memory"
        and (
            parsed_url.hostname
            or parsed_url.path not in {
                "",
                "/",
            }
        )
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "memory:// no debe contener host ni base de datos."
        )

    return normalized_value


def validate_supabase_url(
    value: object,
    setting_name: str = "SUPABASE_URL",
    require_https: bool = False,
) -> str:
    """Valida la URL base del proyecto Supabase."""

    if not isinstance(value, str):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe contener una URL válida de Supabase."
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe contener una URL válida de Supabase."
        )

    parsed_url = urlparse(
        normalized_value
    )

    if parsed_url.scheme not in {
        "http",
        "https",
    }:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe utilizar http o https."
        )

    if (
        require_https
        and parsed_url.scheme != "https"
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "En producción debe utilizar https."
        )

    if not parsed_url.hostname:
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe contener un host válido."
        )

    if (
        parsed_url.path not in {
            "",
            "/",
        }
        or parsed_url.params
        or parsed_url.query
        or parsed_url.fragment
        or parsed_url.username
        or parsed_url.password
    ):
        raise RuntimeError(
            f"{setting_name} no válido. "
            "Debe contener únicamente el esquema y host."
        )

    return normalized_value


def validate_supabase_key(
    value: object,
    setting_name: str = "SUPABASE_KEY",
) -> str:
    """Valida que exista una clave para Supabase."""

    if not isinstance(value, str):
        raise RuntimeError(
            f"{setting_name} no puede estar vacío."
        )

    normalized_value = value.strip()

    if not normalized_value:
        raise RuntimeError(
            f"{setting_name} no puede estar vacío."
        )

    return normalized_value


class Config:
    """Configuración base de la aplicación."""

    ENVIRONMENT = "development"

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-key",
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "dev-jwt-secret-key",
    )

    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(
        os.getenv(
            "JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
            "60",
        )
    )

    DATABASE_URL = normalize_database_url(
        os.getenv("DATABASE_URL")
    )

    TEST_DATABASE_URL = normalize_database_url(
        os.getenv("TEST_DATABASE_URL")
    )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_POOL_SIZE = int(
        os.getenv(
            "SQLALCHEMY_POOL_SIZE",
            "3",
        )
    )

    SQLALCHEMY_MAX_OVERFLOW = int(
        os.getenv(
            "SQLALCHEMY_MAX_OVERFLOW",
            "2",
        )
    )

    SQLALCHEMY_POOL_TIMEOUT = int(
        os.getenv(
            "SQLALCHEMY_POOL_TIMEOUT",
            "10",
        )
    )

    SQLALCHEMY_POOL_RECYCLE = int(
        os.getenv(
            "SQLALCHEMY_POOL_RECYCLE",
            "1800",
        )
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": SQLALCHEMY_POOL_SIZE,
        "max_overflow": SQLALCHEMY_MAX_OVERFLOW,
        "pool_timeout": SQLALCHEMY_POOL_TIMEOUT,
        "pool_recycle": SQLALCHEMY_POOL_RECYCLE,
    }

    WHATSAPP_NUMBER = os.getenv(
        "WHATSAPP_NUMBER",
    )

    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5000",
    )

    STORAGE_PROVIDER = os.getenv(
        "STORAGE_PROVIDER",
        "auto",
    )

    SUPABASE_URL = os.getenv(
        "SUPABASE_URL",
    )

    SUPABASE_KEY = os.getenv(
        "SUPABASE_KEY",
    )

    SUPABASE_STORAGE_BUCKET = os.getenv(
        "SUPABASE_STORAGE_BUCKET",
        "products",
    )

    MAX_IMAGE_SIZE_MB = int(
        os.getenv(
            "MAX_IMAGE_SIZE_MB",
            "5",
        )
    )

    MAX_UPLOAD_REQUEST_OVERHEAD_MB = int(
        os.getenv(
            "MAX_UPLOAD_REQUEST_OVERHEAD_MB",
            "1",
        )
    )

    MAX_CONTENT_LENGTH = (
        MAX_IMAGE_SIZE_MB
        + MAX_UPLOAD_REQUEST_OVERHEAD_MB
    ) * 1024 * 1024

    LOG_LEVEL = os.getenv(
        "LOG_LEVEL",
        "INFO",
    )

    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )

    RATELIMIT_STRATEGY = os.getenv(
        "RATELIMIT_STRATEGY",
        "sliding-window-counter",
    )

    RATELIMIT_HEADERS_ENABLED = False

    RATELIMIT_KEY_PREFIX = os.getenv(
        "RATELIMIT_KEY_PREFIX",
        "loop_and_love",
    )

    LOGIN_RATE_LIMIT_IP = "10 per minute"

    LOGIN_RATE_LIMIT_ACCOUNT = "5 per minute"

    TRUSTED_PROXY_COUNT = int(
        os.getenv(
            "TRUSTED_PROXY_COUNT",
            "0",
        )
    )

    @classmethod
    def validate_security_settings(cls):
        """Valida secretos y configuración criptográfica."""

        secret_key = (
            cls.SECRET_KEY
            if isinstance(
                cls.SECRET_KEY,
                str,
            )
            else ""
        )

        jwt_secret = (
            cls.JWT_SECRET_KEY
            if isinstance(
                cls.JWT_SECRET_KEY,
                str,
            )
            else ""
        )

        if not secret_key.strip():
            raise RuntimeError(
                "SECRET_KEY no puede estar vacío."
            )

        if not jwt_secret.strip():
            raise RuntimeError(
                "JWT_SECRET_KEY no puede estar vacío."
            )

        if cls.ENVIRONMENT == "production":
            forbidden_secret_keys = {
                "dev-secret-key",
                "change-this-secret-key",
                "generate-a-secure-random-secret-at-least-32-bytes",
            }

            forbidden_jwt_secrets = {
                "dev-jwt-secret-key",
                "change-this-secret-key",
                "generate-a-secure-random-secret-at-least-32-bytes",
            }

            if secret_key.strip() in forbidden_secret_keys:
                raise RuntimeError(
                    "SECRET_KEY no puede utilizar "
                    "un valor predeterminado o de ejemplo "
                    "en producción."
                )

            if jwt_secret.strip() in forbidden_jwt_secrets:
                raise RuntimeError(
                    "JWT_SECRET_KEY no puede utilizar "
                    "un valor predeterminado o de ejemplo "
                    "en producción."
                )

            if len(
                secret_key.encode("utf-8")
            ) < 32:
                raise RuntimeError(
                    "SECRET_KEY debe tener al menos 32 bytes "
                    "en producción."
                )

        if len(
            jwt_secret.encode("utf-8")
        ) < 32:
            raise RuntimeError(
                "JWT_SECRET_KEY debe tener al menos 32 bytes."
            )

    @classmethod
    def validate_configuration(
        cls,
        database_url: str | None = None,
    ) -> list[str]:
        """Valida la configuración aplicable al entorno actual."""

        cls.validate_security_settings()

        validate_database_url(
            database_url
            if database_url is not None
            else cls.DATABASE_URL
        )

        provider = (
            cls.STORAGE_PROVIDER
            if isinstance(
                cls.STORAGE_PROVIDER,
                str,
                )
            else ""
        ).strip().lower()

        if provider not in ALLOWED_STORAGE_PROVIDERS:
            allowed = ", ".join(
                sorted(ALLOWED_STORAGE_PROVIDERS)
            )

            raise RuntimeError(
                "STORAGE_PROVIDER no válido. "
                f"Valores permitidos: {allowed}."
            )

        if (
            cls.ENVIRONMENT == "production"
            and provider == "local"
        ):
            raise RuntimeError(
                "STORAGE_PROVIDER no válido. "
                "El almacenamiento local no está permitido "
                "en producción."
            )

        if (
            not isinstance(
                cls.SUPABASE_STORAGE_BUCKET,
                str,
            )
            or not cls.SUPABASE_STORAGE_BUCKET.strip()
        ):
            raise RuntimeError(
                "SUPABASE_STORAGE_BUCKET no válido. "
                "Debe contener un nombre de bucket."
            )

        effective_provider = provider

        if provider == "auto":
            effective_provider = (
                "supabase"
                if cls.ENVIRONMENT == "production"
                else "local"
            )

        if effective_provider == "supabase":
            validate_supabase_url(
                cls.SUPABASE_URL,
                require_https=(
                    cls.ENVIRONMENT == "production"
                ),
            )

            validate_supabase_key(
                cls.SUPABASE_KEY
            )

        cors_origins = parse_cors_origins(
            cls.CORS_ORIGINS
        )

        if (
            cls.ENVIRONMENT == "production"
            and "*" in cors_origins
        ):
            raise RuntimeError(
                "CORS_ORIGINS no válido. "
                "En producción no se permite el origen '*'."
            )

        jwt_expiration = validate_positive_integer(
            cls.JWT_ACCESS_TOKEN_EXPIRES_MINUTES,
            "JWT_ACCESS_TOKEN_EXPIRES_MINUTES",
        )

        max_image_size = validate_positive_integer(
            cls.MAX_IMAGE_SIZE_MB,
            "MAX_IMAGE_SIZE_MB",
        )

        upload_request_overhead = validate_positive_integer(
            cls.MAX_UPLOAD_REQUEST_OVERHEAD_MB,
            "MAX_UPLOAD_REQUEST_OVERHEAD_MB",
        )

        pool_size = validate_positive_integer(
            cls.SQLALCHEMY_POOL_SIZE,
            "SQLALCHEMY_POOL_SIZE",
        )

        max_overflow = validate_non_negative_integer(
            cls.SQLALCHEMY_MAX_OVERFLOW,
            "SQLALCHEMY_MAX_OVERFLOW",
        )

        pool_timeout = validate_positive_integer(
            cls.SQLALCHEMY_POOL_TIMEOUT,
            "SQLALCHEMY_POOL_TIMEOUT",
        )

        pool_recycle = validate_positive_integer(
            cls.SQLALCHEMY_POOL_RECYCLE,
            "SQLALCHEMY_POOL_RECYCLE",
        )

        cls.SQLALCHEMY_POOL_SIZE = pool_size
        cls.SQLALCHEMY_MAX_OVERFLOW = max_overflow
        cls.SQLALCHEMY_POOL_TIMEOUT = pool_timeout
        cls.SQLALCHEMY_POOL_RECYCLE = pool_recycle

        cls.SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle,
        }

        cls.JWT_ACCESS_TOKEN_EXPIRES_MINUTES = (
            jwt_expiration
        )

        cls.MAX_IMAGE_SIZE_MB = (
            max_image_size
        )

        cls.MAX_UPLOAD_REQUEST_OVERHEAD_MB = (
            upload_request_overhead
        )

        cls.MAX_CONTENT_LENGTH = (
            max_image_size
            + upload_request_overhead
        ) * 1024 * 1024

        cls.LOG_LEVEL = validate_log_level(
            cls.LOG_LEVEL
        )

        cls.RATELIMIT_STORAGE_URI = (
            validate_rate_limit_storage_uri(
                cls.RATELIMIT_STORAGE_URI,
                cls.ENVIRONMENT,
            )
        )

        cls.RATELIMIT_STRATEGY = (
            validate_rate_limit_strategy(
                cls.RATELIMIT_STRATEGY
            )
        )

        cls.TRUSTED_PROXY_COUNT = (
            validate_non_negative_integer(
                cls.TRUSTED_PROXY_COUNT,
                "TRUSTED_PROXY_COUNT",
            )
        )

        return cors_origins


class DevelopmentConfig(Config):
    """Configuración de desarrollo local."""

    ENVIRONMENT = "development"
    DEBUG = True


class TestingConfig(Config):
    """Configuración de pruebas de integración."""

    ENVIRONMENT = "testing"
    DEBUG = False
    TESTING = True

    # Las pruebas de Storage continúan utilizando
    # almacenamiento local, salvo que un test específico
    # cree explícitamente el proveedor de Supabase.
    STORAGE_PROVIDER = "local"

    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_STRATEGY = "sliding-window-counter"
    TRUSTED_PROXY_COUNT = 0

    SQLALCHEMY_POOL_SIZE = 2
    SQLALCHEMY_MAX_OVERFLOW = 0
    SQLALCHEMY_POOL_TIMEOUT = 10
    SQLALCHEMY_POOL_RECYCLE = 1800

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 2,
        "max_overflow": 0,
        "pool_timeout": 10,
        "pool_recycle": 1800,
    }


class ProductionConfig(Config):
    """Configuración de producción."""

    ENVIRONMENT = "production"
    DEBUG = False

    TRUSTED_PROXY_COUNT = int(
        os.getenv(
            "TRUSTED_PROXY_COUNT",
            "1",
        )
    )

config_by_environment = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

