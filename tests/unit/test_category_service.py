from types import SimpleNamespace

import pytest

from app.application.services.category_service import (
    CategoryService,
)
from app.domain.normalization import (
    normalize_category_name,
)


class FakeCategoryRepository:
    def __init__(self):
        self.categories = {}
        self.next_id = 1

    def get_by_id(
        self,
        category_id,
    ):
        return self.categories.get(
            category_id
        )

    def get_by_name(
        self,
        name,
    ):
        normalized_name = normalize_category_name(
            name
        )

        for category in self.categories.values():
            if (
                normalize_category_name(
                    category.name
                )
                == normalized_name
            ):
                return category

        return None

    def get_by_slug(
        self,
        slug,
    ):
        for category in self.categories.values():
            if category.slug == slug:
                return category

        return None

    def get_active(self):
        return [
            category
            for category in self.categories.values()
            if category.is_active
        ]

    def get_all(self):
        return list(
            self.categories.values()
        )

    def has_products(
        self,
        category_id,
    ):
        return False

    def create(
        self,
        category,
    ):
        category.id = self.next_id
        self.next_id += 1

        self.categories[
            category.id
        ] = category

        return category

    def update(
        self,
        category,
    ):
        self.categories[
            category.id
        ] = category

        return category

    def delete(
        self,
        category_id,
    ):
        return self.categories.pop(
            category_id,
            None,
        )


def _create_service():
    repository = FakeCategoryRepository()

    return (
        CategoryService(repository),
        repository,
    )


def test_create_category_generates_slug():
    service, repository = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    assert category.id == 1
    assert category.name == "Amigurumis"
    assert category.slug == "amigurumis"
    assert category.is_active is True
    assert repository.categories[1] == category


def test_create_category_removes_accents_from_slug():
    service, _ = _create_service()

    category = service.create_category(
        name="Muñecos de Niño",
    )

    assert category.slug == "munecos-de-nino"


def test_create_category_rejects_duplicate_name():
    service, _ = _create_service()

    service.create_category(
        name="Amigurumis",
    )

    with pytest.raises(ValueError, match="Ya existe"):
        service.create_category(
            name="Amigurumis",
        )


def test_create_category_generates_unique_slug():
    service, _ = _create_service()

    first = service.create_category(
        name="Amigurumis",
    )

    second = service.create_category(
        name="Amigurumis-2",
    )

    assert first.slug == "amigurumis"
    assert second.slug == "amigurumis-2"


def test_create_category_generates_suffix_when_slug_exists():
    service, repository = _create_service()

    service.create_category(
        name="Amigurumis",
    )

    repository.categories[2] = SimpleNamespace(
        id=2,
        name="Otra categoría",
        slug="amigurumis-2",
        is_active=True,
    )

    repository.next_id = 3

    category = service.create_category(
        name="Amigurumis-2",
    )

    assert category.slug == "amigurumis-2-2"


def test_get_category_returns_category():
    service, _ = _create_service()

    created = service.create_category(
        name="Amigurumis",
    )

    result = service.get_category(
        created.id
    )

    assert result == created


def test_get_category_returns_none_when_not_found():
    service, _ = _create_service()

    result = service.get_category(999)

    assert result is None


def test_list_active_categories():
    service, _ = _create_service()

    active = service.create_category(
        name="Amigurumis",
        is_active=True,
    )

    service.create_category(
        name="Decoración",
        is_active=False,
    )

    result = service.list_active_categories()

    assert result == [active]


def test_update_category():
    service, _ = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    updated = service.update_category(
        category_id=category.id,
        name="Muñecos",
        is_active=False,
    )

    assert updated.id == category.id
    assert updated.name == "Muñecos"
    assert updated.slug == "munecos"
    assert updated.is_active is False


def test_update_category_rejects_duplicate_name():
    service, _ = _create_service()

    first = service.create_category(
        name="Amigurumis",
    )

    second = service.create_category(
        name="Decoración",
    )

    with pytest.raises(ValueError, match="Ya existe"):
        service.update_category(
            category_id=second.id,
            name=first.name,
            is_active=True,
        )


def test_update_nonexistent_category():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="La categoría no existe",
    ):
        service.update_category(
            category_id=999,
            name="Amigurumis",
            is_active=True,
        )


def test_delete_category():
    service, repository = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    deleted = service.delete_category(
        category.id
    )

    assert deleted == category
    assert category.id not in repository.categories


def test_delete_nonexistent_category():
    service, _ = _create_service()

    with pytest.raises(
        LookupError,
        match="La categoría no existe",
    ):
        service.delete_category(999)


def test_category_name_is_trimmed():
    service, _ = _create_service()

    category = service.create_category(
        name="  Amigurumis  ",
    )

    assert category.name == "Amigurumis"


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_create_category_rejects_invalid_name(name):
    service, _ = _create_service()

    with pytest.raises(ValueError):
        service.create_category(
            name=name,
        )


def test_create_category_rejects_invalid_is_active():
    service, _ = _create_service()

    with pytest.raises(ValueError):
        service.create_category(
            name="Amigurumis",
            is_active="true",
        )


def test_get_category_rejects_invalid_id():
    service, _ = _create_service()

    with pytest.raises(ValueError):
        service.get_category(0)

    with pytest.raises(ValueError):
        service.get_category(-1)

    with pytest.raises(ValueError):
        service.get_category("1")


def test_update_category_keeps_slug_when_name_same():
    service, _ = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    updated = service.update_category(
        category_id=category.id,
        name="Amigurumis",
        is_active=True,
    )

    assert updated.slug == "amigurumis"

def test_delete_category_rejects_category_with_products():
    service, repository = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    repository.has_products = (
        lambda category_id: True
    )

    with pytest.raises(
        ValueError,
        match="tiene productos asociados",
    ):
        service.delete_category(
            category.id
        )

def test_delete_category_without_products():
    service, repository = _create_service()

    category = service.create_category(
        name="Amigurumis",
    )

    deleted = service.delete_category(
        category.id
    )

    assert deleted.id == category.id
    assert (
        category.id
        not in repository.categories
    )

def test_category_name_normalizes_internal_spaces():
    service, _ = _create_service()

    category = service.create_category(
        "  Amigurumis   Crochet  "
    )

    assert (
        category.name
        == "Amigurumis Crochet"
    )

    assert (
        category.slug
        == "amigurumis-crochet"
    )

def test_category_name_is_case_insensitive():
    service, _ = _create_service()

    first = service.create_category(
        "Amigurumis"
    )

    with pytest.raises(
        ValueError,
        match="Ya existe una categoría con ese nombre",
    ):
        service.create_category(
            "AMIGURUMIS"
        )

    assert first.name == "Amigurumis"