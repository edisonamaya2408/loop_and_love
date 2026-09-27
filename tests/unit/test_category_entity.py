from datetime import datetime, timezone

from app.domain.entities.category import CategoryEntity


def test_category_entity_creation():
    now = datetime.now(timezone.utc)

    category = CategoryEntity(
        id=1,
        name="Amigurumis",
        slug="amigurumis",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    assert category.id == 1
    assert category.name == "Amigurumis"
    assert category.slug == "amigurumis"
    assert category.is_active is True
    assert category.created_at == now
    assert category.updated_at == now