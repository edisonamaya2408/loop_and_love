from flask import (
    current_app,
    has_app_context,
)

from app.config.settings import Config
from app.domain.repositories.storage_repository import (
    StorageRepository,
)
from app.infrastructure.storage.local_storage_repository import (
    LocalStorageRepository,
)
from app.infrastructure.storage.supabase_storage_repository import (
    SupabaseStorageRepository,
)


def _get_storage_setting(
    name: str,
):
    """
    Obtiene una configuración desde la aplicación Flask
    cuando existe contexto; de lo contrario utiliza Config.

    Esto permite que ProductionConfig / TestingConfig /
    DevelopmentConfig sean respetadas correctamente.
    """

    if has_app_context():
        value = current_app.config.get(
            name
        )

        if value is not None:
            return value

    return getattr(
        Config,
        name,
    )


def create_storage_repository() -> StorageRepository:
    """
    Crea el proveedor de almacenamiento configurado.

    STORAGE_PROVIDER:
        auto
        local
        supabase

    auto:
        development/testing -> local
        production          -> supabase
    """

    provider = _get_storage_setting(
        "STORAGE_PROVIDER"
    )

    environment = _get_storage_setting(
        "ENVIRONMENT"
    )

    provider = (
        provider
        if isinstance(
            provider,
            str,
        )
        else ""
    ).strip().lower()

    environment = (
        environment
        if isinstance(
            environment,
            str,
        )
        else ""
    ).strip().lower()

    if provider == "auto":
        provider = (
            "supabase"
            if environment == "production"
            else "local"
        )

    if (
        environment == "production"
        and provider == "local"
    ):
        raise RuntimeError(
            "STORAGE_PROVIDER no válido. "
            "El almacenamiento local no está permitido "
            "en producción."
        )

    if provider == "local":
        return LocalStorageRepository()

    if provider == "supabase":
        return SupabaseStorageRepository()

    raise RuntimeError(
        "STORAGE_PROVIDER no válido. "
        "Valores permitidos: auto, local, supabase."
    )