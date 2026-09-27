from datetime import datetime, timezone

from sqlalchemy import Unicode, UnicodeText
from sqlalchemy.orm import validates

from app.domain.normalization import (
    normalize_product_code,
)
from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class Product(db.Model):
    """Modelo de persistencia para los productos de Loop & Love."""

    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    code = db.Column(
        Unicode(50),
        nullable=False,
    )

    name = db.Column(
        Unicode(150),
        nullable=False,
    )

    description = db.Column(
        UnicodeText,
        nullable=True,
    )

    price = db.Column(
        db.Numeric(12, 2),
        nullable=False,
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "categories.id",
            name="fk_products_category_id_categories",
        ),
        nullable=False,
    )

    category = db.relationship(
        "Category",
        lazy="joined",
    )

    image_url = db.Column(
        Unicode(500),
        nullable=True,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    created_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "code",
            name="uq_products_code",
        ),
    )

    @validates("code")
    def validate_code(
        self,
        key,
        value,
    ):
        return normalize_product_code(
            value
        )

    def __repr__(self):
        return (
            f"<Product {self.id}: "
            f"{self.code} - {self.name}>"
        )