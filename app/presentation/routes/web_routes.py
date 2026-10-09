import os

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    url_for,
)

from app.application.services.admin_setup_service import (
    AdminSetupService,
)
from app.domain.exceptions import (
    AdminSetupNotRequiredError,
    AdminSetupUnavailableError,
    InvalidAdminSetupTokenError,
)
from app.infrastructure.database.repositories import (
    SQLAlchemyAdminUserRepository,
)
from app.extensions import limiter


web_bp = Blueprint(
    "web",
    __name__,
)


def _get_admin_user_repository():
    """
    Permite inyectar un repositorio durante pruebas.

    En ejecución normal utiliza SQLAlchemy.
    """

    repository = current_app.extensions.get(
        "admin_user_repository"
    )

    if repository is not None:
        return repository

    return SQLAlchemyAdminUserRepository()


def _get_admin_setup_service():
    return AdminSetupService(
        repository=_get_admin_user_repository(),
        setup_token=os.getenv(
            "ADMIN_SETUP_TOKEN"
        ),
    )


def _setup_required():
    return (
        _get_admin_setup_service()
        .setup_required()
    )


@web_bp.get("/")
def public_home():
    """
    Página principal pública de Loop & Love.
    """

    return render_template(
        "public/index.html"
    )


@web_bp.get("/admin")
@web_bp.get("/admin/")
def admin_entry():
    """
    Entrada del portal administrativo.

    Si todavía no existe ningún administrador,
    se dirige al proceso de configuración inicial.

    Una vez creado el primer administrador, siempre
    dirige al login.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return redirect(
        url_for(
            "web.admin_login"
        )
    )


@web_bp.get("/admin/setup")
def admin_setup():
    """
    Formulario para crear el primer administrador.
    """

    if not _setup_required():
        return redirect(
            url_for(
                "web.admin_login"
            )
        )

    setup_token_configured = bool(
        os.getenv(
            "ADMIN_SETUP_TOKEN"
        )
    )

    return render_template(
        "admin/setup.html",
        setup_token_configured=(
            setup_token_configured
        ),
        error_message=None,
        form_name="",
        form_email="",
    )


@web_bp.post("/admin/setup")
@limiter.limit(
    "5 per hour"
)
def admin_setup_submit():
    """
    Procesa la creación inicial del administrador.

    El endpoint está protegido por un secreto de bootstrap
    almacenado como variable de entorno.
    """

    service = _get_admin_setup_service()

    form_name = (
        request.form.get(
            "name",
            "",
        ).strip()
    )

    form_email = (
        request.form.get(
            "email",
            "",
        )
        .strip()
    )

    setup_token = (
        request.form.get(
            "setup_token",
            "",
        )
    )

    password = request.form.get(
        "password",
        "",
    )

    password_confirmation = request.form.get(
        "password_confirmation",
        "",
    )

    try:
        service.create_initial_admin(
            setup_token=setup_token,
            name=form_name,
            email=form_email,
            password=password,
            password_confirmation=(
                password_confirmation
            ),
        )

    except AdminSetupNotRequiredError:
        return redirect(
            url_for(
                "web.admin_login"
            )
        )

    except AdminSetupUnavailableError as error:
        return render_template(
            "admin/setup.html",
            setup_token_configured=False,
            error_message=str(error),
            form_name=form_name,
            form_email=form_email,
        ), 503

    except InvalidAdminSetupTokenError as error:
        return render_template(
            "admin/setup.html",
            setup_token_configured=True,
            error_message=str(error),
            form_name=form_name,
            form_email=form_email,
        ), 401

    except ValueError as error:
        return render_template(
            "admin/setup.html",
            setup_token_configured=True,
            error_message=str(error),
            form_name=form_name,
            form_email=form_email,
        ), 400

    return redirect(
        url_for(
            "web.admin_login",
            created="1",
        )
    )


@web_bp.get("/admin/login")
def admin_login():
    """
    Página de inicio de sesión administrativa.

    Si no existe ningún administrador, el login no se muestra;
    se utiliza directamente el bootstrap inicial.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    created = (
        request.args.get(
            "created"
        )
        == "1"
    )

    return render_template(
        "admin/login.html",
        setup_created=created,
    )


@web_bp.get("/admin/dashboard")
def admin_dashboard():
    """
    Dashboard principal del portal administrativo.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return render_template(
        "admin/dashboard.html"
    )


@web_bp.get("/admin/users")
def admin_users_page():
    """
    Página de administración de usuarios.

    La autenticación efectiva de las operaciones se realiza
    mediante JWT en la API. Esta ruta únicamente entrega
    la interfaz; admin-users.js verifica que exista un token
    antes de consumir los endpoints protegidos.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return render_template(
        "admin/users.html"
    )


@web_bp.get("/admin/categories")
def admin_categories_page():
    """
    Página de administración de categorías.

    La autenticación efectiva de las operaciones se realiza
    mediante JWT en la API. Esta ruta únicamente entrega
    la interfaz; admin-categories.js verifica que exista
    un token antes de consumir los endpoints protegidos.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return render_template(
        "admin/categories.html"
    )


@web_bp.get("/admin/products")
def admin_products_page():
    """
    Página de administración de productos.

    La autenticación efectiva de las operaciones se realiza
    mediante JWT en la API. Esta ruta únicamente entrega
    la interfaz; admin-products.js verifica que exista
    un token antes de consumir los endpoints protegidos.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return render_template(
        "admin/products.html"
    )

@web_bp.get("/admin/orders")
def admin_orders_page():
    """
    Página de administración de pedidos.

    La autenticación efectiva de las operaciones se realiza
    mediante JWT en la API. Esta ruta únicamente entrega
    la interfaz; admin-orders.js verifica que exista un token
    antes de consumir el endpoint protegido.
    """

    if _setup_required():
        return redirect(
            url_for(
                "web.admin_setup"
            )
        )

    return render_template(
        "admin/orders.html"
    )


@web_bp.get("/admin/audit-logs")
def admin_audit_logs_page():
    """Página de consulta de auditoría administrativa."""

    if _setup_required():
        return redirect(
            url_for("web.admin_setup")
        )

    return render_template(
        "admin/audit_logs.html"
    )