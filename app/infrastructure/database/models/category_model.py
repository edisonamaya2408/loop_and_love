from datetime import datetime, timezone

from sqlalchemy import Unicode
from sqlalchemy.orm import validates

from app.domain.normalization import (
    normalize_category_display_name,
    normalize_category_name,
)
from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class Category(db.Model):
    """Modelo de persistencia para las categorías."""

    __tablename__ = "categories"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    name = db.Column(
        Unicode(100),
        nullable=False,
    )

    name_normalized = db.Column(
        Unicode(100),
        nullable=False,
    )

    slug = db.Column(
        Unicode(100),
        nullable=False,
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
            "name_normalized",
            name="uq_categories_name_normalized",
        ),
        db.UniqueConstraint(
            "slug",
            name="uq_categories_slug",
        ),
    )

    @validates("name")
    def validate_name(
        self,
        key,
        value,
    ):
        """
        Normaliza automáticamente el nombre visible
        y mantiene sincronizada su clave canónica.
        """

        display_name = normalize_category_display_name(
            value
        )

        self.name_normalized = (
            normalize_category_name(
                display_name
            )
        )

        return display_name

    def __repr__(self):
        return (
            f"<Category {self.id}: "
            f"{self.name} ({self.slug})>"
        )