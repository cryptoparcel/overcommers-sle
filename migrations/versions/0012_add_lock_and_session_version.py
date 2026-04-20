"""Add is_locked and session_version to users.

Revision ID: 0012
Revises: 0011
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )
        batch.add_column(
            sa.Column("session_version", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("session_version")
        batch.drop_column("is_locked")
