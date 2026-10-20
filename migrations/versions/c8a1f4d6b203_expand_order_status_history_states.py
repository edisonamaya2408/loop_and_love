"""Expand allowed order status history states.

Revision ID: c8a1f4d6b203
Revises: b7c4e1d8a206
"""

from alembic import op
import sqlalchemy as sa


revision = "c8a1f4d6b203"
down_revision = "b7c4e1d8a206"
branch_labels = None
depends_on = None


def upgrade():
    # Eliminar las restricciones antiguas.
    op.drop_constraint(
        "ck_order_status_history_previous_status",
        "order_status_history",
        type_="check",
    )

    op.drop_constraint(
        "ck_order_status_history_new_status",
        "order_status_history",
        type_="check",
    )

    # Permitir los seis estados en el estado anterior.
    op.create_check_constraint(
        "ck_order_status_history_previous_status",
        "order_status_history",
        """
        previous_status IS NULL
        OR previous_status IN (
            'pending',
            'confirmed',
            'preparing',
            'shipped',
            'delivered',
            'cancelled'
        )
        """,
    )

    # Permitir los seis estados en el nuevo estado.
    op.create_check_constraint(
        "ck_order_status_history_new_status",
        "order_status_history",
        """
        new_status IN (
            'pending',
            'confirmed',
            'preparing',
            'shipped',
            'delivered',
            'cancelled'
        )
        """,
    )


def downgrade():
    # No revertir si ya existe historial con nuevos estados.
    # Esto evita perder información de auditoría.
    result = op.get_bind().execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM order_status_history
            WHERE
                (
                    previous_status IS NOT NULL
                    AND previous_status NOT IN (
                        'pending',
                        'confirmed',
                        'cancelled'
                    )
                )
                OR new_status NOT IN (
                    'pending',
                    'confirmed',
                    'cancelled'
                )
            """
        )
    )

    invalid_history_count = result.scalar() or 0

    if invalid_history_count:
        raise RuntimeError(
            "No se puede revertir esta migración: "
            "existe historial con estados nuevos. "
            "Se conserva la información de auditoría."
        )

    op.drop_constraint(
        "ck_order_status_history_previous_status",
        "order_status_history",
        type_="check",
    )

    op.drop_constraint(
        "ck_order_status_history_new_status",
        "order_status_history",
        type_="check",
    )

    # Restaurar las restricciones originales.
    op.create_check_constraint(
        "ck_order_status_history_previous_status",
        "order_status_history",
        """
        previous_status IS NULL
        OR previous_status IN (
            'pending',
            'confirmed',
            'cancelled'
        )
        """,
    )

    op.create_check_constraint(
        "ck_order_status_history_new_status",
        "order_status_history",
        """
        new_status IN (
            'pending',
            'confirmed',
            'cancelled'
        )
        """,
    )