import getpass
import logging
import os

from flask import Flask, jsonify
from sqlalchemy import text

from app.config.logging_config import configure_logging
from app.config.settings import (
    config_by_environment,
    get_database_url,
)
from app.extensions import (
    cors,
    db,
    limiter,
    migrate,
)
from werkzeug.middleware.proxy_fix import (
    ProxyFix,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyAdminUserRepository,
)
from app.infrastructure.security.password_service import (
    PasswordService,
)
from app.infrastructure.storage.storage_factory import (
    create_storage_repository,
)
from app.presentation.middleware.auth_middleware import (
    jwt_required,
)
from app.presentation.middleware.error_handler import (
    register_error_handlers,
)
from app.presentation.middleware.request_logging import (
    register_request_logging,
)
from app.presentation.routes.admin_category_routes import (
    admin_categories_bp,
)
from app.presentation.routes.order_routes import (
    orders_bp,
)
from app.presentation.routes.admin_order_routes import (
    admin_orders_bp,
)
from app.presentation.routes.admin_product_routes import (
    admin_products_bp,
)
from app.presentation.routes.admin_user_routes import (
    admin_users_bp,
)
from app.presentation.routes.auth_routes import (
    auth_bp,
)
from app.presentation.routes.category_routes import (
    categories_bp,
)
from app.presentation.routes.product_routes import (
    products_bp,
)
from app.presentation.routes.web_routes import (
    web_bp,
)
from app.domain.exceptions import (
    StorageOperationError,
)


logger = logging.getLogger(__name__)


def create_app(environment=None):
    """
    Application Factory de Flask.

    Permite crear diferentes instancias de la aplicación
    según el entorno de ejecución.
    """

    if environment is None:
        environment = os.getenv(
            "APP_ENV",
            os.getenv(
                "FLASK_ENV",
                "development",
            ),
        )

    environment = environment.strip().lower()

    if environment not in config_by_environment:
        raise RuntimeError(
            "APP_ENV no válido. "
            "Valores permitidos: development, testing, production."
        )

    config_class = config_by_environment[
        environment
    ]

    app = Flask(
        __name__,
        template_folder="web/templates",
        static_folder="web/static",
    )

    app.config.from_object(
        config_class
    )

    if (
        config_class.TRUSTED_PROXY_COUNT
        > 0
    ):
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=(
                config_class.TRUSTED_PROXY_COUNT
            ),
        )

    database_url = get_database_url(
        environment
    )

    if not database_url:
        if environment == "testing":
            raise RuntimeError(
                "TEST_DATABASE_URL es obligatorio "
                "para el entorno de pruebas."
            )

        raise RuntimeError(
            "DATABASE_URL es obligatorio "
            "para el entorno de aplicación."
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url
    )

    cors_origins = config_class.validate_configuration(
        database_url=database_url
    )

    configure_logging(
        config_class.LOG_LEVEL
    )

    app.config["MAX_CONTENT_LENGTH"] = (
        config_class.MAX_CONTENT_LENGTH
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url
    )

    app.config["CORS_ORIGINS_LIST"] = (
        cors_origins
    )

    db.init_app(app)

    migrate.init_app(
        app,
        db,
    )

    limiter.init_app(
        app
    )

    cors.init_app(
        app,
        origins=cors_origins,
    )

    register_error_handlers(
        app
    )

    app.register_blueprint(
        web_bp
    )

    app.register_blueprint(
        products_bp
    )

    app.register_blueprint(
        auth_bp
    )

    app.register_blueprint(
        admin_products_bp
    )

    app.register_blueprint(
        admin_users_bp
    )

    app.register_blueprint(
        categories_bp
    )

    app.register_blueprint(
        orders_bp
    )

    app.register_blueprint(
        admin_orders_bp
    )

    app.register_blueprint(
        admin_categories_bp
    )

    register_request_logging(
        app
    )

    @app.get("/health")
    def health_check():
        """
        Liveness check público.

        Este endpoint no consulta servicios externos
        ni expone información de infraestructura.
        """

        return jsonify(
            {
                "success": True,
                "status": "ok",
                "message": (
                    "Loop & Love API "
                    "funcionando correctamente."
                ),
            }
        ), 200

    @app.get("/health/db")
    @jwt_required
    def database_health_check():
        """
        Readiness check de base de datos.

        Requiere autenticación administrativa y no
        expone nombre de base de datos, driver,
        entorno ni detalles internos de la excepción.
        """

        try:
            db.session.execute(
                text("SELECT 1")
            )

            return jsonify(
                {
                    "success": True,
                    "status": "ok",
                    "message": (
                        "Conexión con la base de datos "
                        "funcionando correctamente."
                    ),
                }
            ), 200

        except Exception as error:
            db.session.rollback()

            logger.error(
                "Database health check failed "
                "exception_type=%s",
                type(error).__name__,
            )

            return jsonify(
                {
                    "success": False,
                    "status": "error",
                    "message": (
                        "No fue posible verificar "
                        "la conexión con la base de datos."
                    ),
                }
            ), 500

    @app.get("/health/storage")
    @jwt_required
    def storage_health_check():
        """
        Readiness check del almacenamiento.

        Requiere autenticación administrativa y no
        expone proveedor, entorno ni detalles internos
        de la excepción.
        """

        try:
            storage_repository = (
                create_storage_repository()
            )

            storage_repository.health_check()

            return jsonify(
                {
                    "success": True,
                    "status": "ok",
                    "message": (
                        "Almacenamiento funcionando "
                        "correctamente."
                    ),
                }
            ), 200

        except StorageOperationError:
            raise

        except Exception as error:
            logger.error(
                "Storage health check failed "
                "exception_type=%s",
                type(error).__name__,
            )

            return jsonify(
                {
                    "success": False,
                    "status": "error",
                    "message": (
                        "No fue posible verificar "
                        "el almacenamiento."
                    ),
                }
            ), 500

    @app.cli.command("create-admin")
    def create_admin():
        """Crea el usuario administrador inicial."""

        from app.domain.entities.admin_user import (
            AdminUserEntity,
        )

        email = input(
            "Correo del administrador: "
        ).strip().lower()

        if not email:
            print(
                "El correo es obligatorio."
            )
            return

        password = getpass.getpass(
            "Contraseña: "
        )

        password_confirmation = (
            getpass.getpass(
                "Confirmar contraseña: "
            )
        )

        if password != password_confirmation:
            print(
                "Las contraseñas no coinciden."
            )
            return

        if len(password) < 8:
            print(
                "La contraseña debe tener al menos "
                "8 caracteres."
            )
            return

        repository = (
            SQLAlchemyAdminUserRepository()
        )

        existing_user = (
            repository.get_by_email(
                email
            )
        )

        if existing_user is not None:
            print(
                "Ya existe un usuario administrador "
                "con ese correo."
            )
            return

        admin_user = AdminUserEntity(
            id=None,
            email=email,
            password_hash=(
                PasswordService.hash_password(
                    password
                )
            ),
            is_active=True,
        )

        repository.create(
            admin_user
        )

        print(
            "Usuario administrador creado correctamente."
        )

    return app