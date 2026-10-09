"""add admin user display name

Revision ID: c7e4a2f918d0
Revises: b4d7e9f2a1c6
"""

import re

from alembic import op
import sqlalchemy as sa


revision = "c7e4a2f918d0"
down_revision = "b4d7e9f2a1c6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "admin_users",
        sa.Column(
            "name",
            sa.Unicode(length=120),
            nullable=True,
        ),
    )

    bind = op.get_bind()

    rows = bind.execute(
        sa.text(
            "SELECT id, email FROM admin_users"
        )
    ).mappings().all()

    for row in rows:
        email = str(
            row["email"] or ""
        )

        local_part = email.split(
            "@",
            1,
        )[0]

        parts = [
            part
            for part in re.split(
                r"[._+-]+",
                local_part,
            )
            if part
        ]

        display_name = " ".join(
            part[:1].upper() + part[1:]
            for part in parts
        ).strip()

        display_name = (
            display_name[:120]
            or "Administrador"
        )

        bind.execute(
            sa.text(
                """
                UPDATE admin_users
                SET name = :name
                WHERE id = :id
                """
            ),
            {
                "name": display_name,
                "id": row["id"],
            },
        )

    op.alter_column(
        "admin_users",
        "name",
        existing_type=sa.Unicode(length=120),
        existing_nullable=True,
        nullable=False,
    )


def downgrade():
    op.drop_column(
        "admin_users",
        "name",
    )