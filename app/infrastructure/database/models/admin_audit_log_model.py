from datetime import datetime, timezone

from sqlalchemy import Unicode, UnicodeText

from app.extensions import db
from app.infrastructure.database.types import UTCDateTime


class AdminAuditLog(db.Model):
    """Registro persistente de operaciones administrativas."""

    __tablename__ = "admin_audit_logs"

    __table_args__ = (
        db.Index(
            "ix_admin_audit_logs_created_at",
            "created_at",
        ),
        db.Index(
            "ix_admin_audit_logs_actor_created_at",
            "actor_id",
            "created_at",
        ),
        db.Index(
            "ix_admin_audit_logs_entity_created_at",
            "entity_type",
            "entity_id",
            "created_at",
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "admin_users.id",
            name="fk_admin_audit_logs_actor_id_admin_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # Se conserva la identidad histórica aunque cambie el
    # nombre/correo del administrador o su cuenta se desactive.
    actor_name = db.Column(
        Unicode(120),
        nullable=False,
    )

    actor_email = db.Column(
        Unicode(255),
        nullable=False,
    )

    # Ejemplos: product.created, order.confirmed.
    action = db.Column(
        Unicode(80),
        nullable=False,
    )

    # product, category, order, admin_user.
    entity_type = db.Column(
        Unicode(40),
        nullable=False,
    )

    # Se almacena como texto para aceptar distintos tipos de ID.
    entity_id = db.Column(
        Unicode(64),
        nullable=True,
    )

    # JSON serializado por el repositorio.
    details_json = db.Column(
        UnicodeText,
        nullable=False,
    )

    ip_address = db.Column(
        Unicode(45),
        nullable=True,
    )

    request_id = db.Column(
        Unicode(64),
        nullable=True,
    )

    created_at = db.Column(
        UTCDateTime(),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    def __repr__(self):
        return (
            f"<AdminAuditLog "
            f"{self.id}: {self.action} "
            f"{self.entity_type}:{self.entity_id}>"
        )