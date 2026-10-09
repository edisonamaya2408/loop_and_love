from datetime import datetime, timezone

from sqlalchemy import Unicode, text
from sqlalchemy.orm import validates

from app.domain.normalization import (
    normalize_admin_display_name,
    normalize_email,
)
from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class AdminUser(db.Model):
    """Modelo de persistencia para usuarios administrativos."""

    __tablename__ = "admin_users"

    __table_args__ = (
        db.CheckConstraint(
            "token_version >= 0",
            name="ck_admin_users_token_version_non_negative",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    name = db.Column(
        Unicode(120),
        nullable=False,
    )

    email = db.Column(
        Unicode(255),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = db.Column(
        Unicode(255),
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

    token_version = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
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

    @validates("email")
    def validate_email(
        self,
        key,
        value,
    ):
        return normalize_email(
            value
        )

    @validates("name")
    def validate_name(
        self,
        key,
        value,
    ):
        return normalize_admin_display_name(
            value
        )

    def __repr__(self):
        return (
            f"<AdminUser {self.id}: {self.email}>"
        )