from datetime import datetime, timezone

from sqlalchemy.sql.sqltypes import Unicode, UnicodeText

from app.infrastructure.database.models.admin_user_model import (
    AdminUser,
)
from app.infrastructure.database.models.category_model import (
    Category,
)
from app.infrastructure.database.models.product_model import (
    Product,
)
from app.infrastructure.database.types import UTCDateTime


def test_admin_user_uses_unicode_email():
    assert isinstance(
        AdminUser.__table__.c.email.type,
        Unicode,
    )


def test_admin_user_uses_utc_datetime_type():
    assert isinstance(
        AdminUser.__table__.c.created_at.type,
        UTCDateTime,
    )

    assert isinstance(
        AdminUser.__table__.c.updated_at.type,
        UTCDateTime,
    )


def test_category_uses_unicode_fields():
    assert isinstance(
        Category.__table__.c.name.type,
        Unicode,
    )

    assert isinstance(
        Category.__table__.c.slug.type,
        Unicode,
    )


def test_category_uses_utc_datetime_type():
    assert isinstance(
        Category.__table__.c.created_at.type,
        UTCDateTime,
    )

    assert isinstance(
        Category.__table__.c.updated_at.type,
        UTCDateTime,
    )


def test_product_uses_unicode_fields():
    assert isinstance(
        Product.__table__.c.code.type,
        Unicode,
    )

    assert isinstance(
        Product.__table__.c.name.type,
        Unicode,
    )

    assert isinstance(
        Product.__table__.c.description.type,
        UnicodeText,
    )

    assert isinstance(
        Product.__table__.c.image_url.type,
        Unicode,
    )


def test_product_uses_utc_datetime_type():
    assert isinstance(
        Product.__table__.c.created_at.type,
        UTCDateTime,
    )

    assert isinstance(
        Product.__table__.c.updated_at.type,
        UTCDateTime,
    )


def test_utc_datetime_converts_aware_value_to_utc_naive():
    utc_type = UTCDateTime()

    value = datetime(
        2026,
        9,
        17,
        10,
        30,
        45,
        tzinfo=timezone.utc,
    )

    result = utc_type.process_bind_param(
        value,
        None,
    )

    assert result == datetime(
        2026,
        9,
        17,
        10,
        30,
        45,
    )

    assert result.tzinfo is None


def test_utc_datetime_converts_naive_value_to_utc():
    utc_type = UTCDateTime()

    value = datetime(
        2026,
        9,
        17,
        10,
        30,
        45,
    )

    result = utc_type.process_bind_param(
        value,
        None,
    )

    assert result == value

    assert result.tzinfo is None


def test_utc_datetime_restores_utc_timezone():
    utc_type = UTCDateTime()

    value = datetime(
        2026,
        9,
        17,
        10,
        30,
        45,
    )

    result = utc_type.process_result_value(
        value,
        None,
    )

    assert result == datetime(
        2026,
        9,
        17,
        10,
        30,
        45,
        tzinfo=timezone.utc,
    )

    assert result.tzinfo == timezone.utc

def test_category_has_normalized_name():
    assert (
        "name_normalized"
        in Category.__table__.c
    )


def test_category_uses_normalized_name_unique_constraint():
    constraints = {
        constraint.name
        for constraint
        in Category.__table__.constraints
        if constraint.name is not None
    }

    assert (
        "uq_categories_name_normalized"
        in constraints
    )