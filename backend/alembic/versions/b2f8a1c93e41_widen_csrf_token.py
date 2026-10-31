"""widen csrf token column

Revision ID: b2f8a1c93e41
Revises: f114c336725b
Create Date: 2026-10-31 16:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2f8a1c93e41"
down_revision: Union[str, None] = "f114c336725b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "auth_sessions",
        "csrf_token",
        existing_type=sa.String(length=64),
        type_=sa.String(length=128),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "auth_sessions",
        "csrf_token",
        existing_type=sa.String(length=128),
        type_=sa.String(length=64),
        existing_nullable=False,
    )

