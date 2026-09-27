import pytest
from sqlalchemy import inspect, text

from app.extensions import db


@pytest.mark.integration
def test_database_connection(app):
    with app.app_context():
        result = db.session.execute(
            text("SELECT 1")
        ).scalar_one()

        assert result == 1


@pytest.mark.integration
def test_required_tables_exist(app):
    with app.app_context():
        inspector = inspect(db.engine)

        tables = set(
            inspector.get_table_names()
        )

        assert {
            "admin_users",
            "categories",
            "products",
        }.issubset(tables)


@pytest.mark.integration
def test_products_category_foreign_key_exists(app):
    with app.app_context():
        inspector = inspect(db.engine)

        foreign_keys = inspector.get_foreign_keys(
            "products"
        )

        matching_foreign_keys = [
            foreign_key
            for foreign_key in foreign_keys
            if foreign_key.get("name")
            == "fk_products_category_id_categories"
            and foreign_key.get("referred_table")
            == "categories"
            and foreign_key.get("constrained_columns")
            == ["category_id"]
            and foreign_key.get("referred_columns")
            == ["id"]
        ]

        assert matching_foreign_keys