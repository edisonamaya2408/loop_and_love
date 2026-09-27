import pytest

from app.infrastructure.database.models.category_model import (
    Category,
)


@pytest.mark.integration
def test_integration_session_discards_uncommitted_changes_when_closed(
    app,
    integration_session,
):
    with app.app_context():
        category = Category(
            name="Integration Session Rollback Test",
            slug="integration-session-rollback-test",
            is_active=True,
        )

        integration_session.add(category)
        integration_session.flush()

        category_id = category.id

        assert category_id is not None

        persisted = integration_session.get(
            Category,
            category_id,
        )

        assert persisted is not None

        assert (
            persisted.slug
            == "integration-session-rollback-test"
        )

    # La fixture cierra la sesión al terminar el test.
    # Los cambios no confirmados deben descartarse al
    # cerrarse la sesión.


@pytest.mark.integration
def test_new_integration_session_does_not_see_uncommitted_changes(
    app,
    integration_session,
):
    with app.app_context():
        result = (
            integration_session.query(Category)
            .filter(
                Category.slug
                == "integration-session-rollback-test"
            )
            .first()
        )

        assert result is None