import pytest

from app.domain.entities.admin_audit_event import (
    AdminAuditEventEntity,
)
from app.infrastructure.database.models.admin_audit_log_model import (
    AdminAuditLog,
)
from app.infrastructure.database.repositories.admin_audit_repository_impl import (
    SQLAlchemyAdminAuditRepository,
)


@pytest.mark.integration
def test_admin_audit_event_persists_and_deserializes(
    integration_session,
):
    repository = SQLAlchemyAdminAuditRepository(
        session=integration_session
    )

    event = AdminAuditEventEntity(
        id=None,
        actor_id=None,
        actor_name="Administrador de integración",
        actor_email="audit-test@example.com",
        action="product.created",
        entity_type="product",
        entity_id="900001",
        details={
            "fields": {
                "name": "Producto de integración",
                "is_active": True,
            }
        },
        ip_address="127.0.0.1",
        request_id="audit-integration-test",
    )

    created = None

    try:
        created = repository.record(
            event
        )

        assert created.id is not None

        persisted = (
            integration_session.query(
                AdminAuditLog
            )
            .filter(
                AdminAuditLog.id == created.id
            )
            .one()
        )

        restored = (
            repository._to_entity(
                persisted
            )
        )

        assert (
            restored.actor_name
            == "Administrador de integración"
        )

        assert (
            restored.actor_email
            == "audit-test@example.com"
        )

        assert restored.action == "product.created"

        assert restored.entity_type == "product"

        assert restored.entity_id == "900001"

        assert (
            restored.details["fields"]["name"]
            == "Producto de integración"
        )

        assert (
            restored.request_id
            == "audit-integration-test"
        )

    finally:
        if created is not None:
            (
                integration_session.query(
                    AdminAuditLog
                )
                .filter(
                    AdminAuditLog.id == created.id
                )
                .delete(
                    synchronize_session=False
                )
            )

            integration_session.commit()