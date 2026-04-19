"""Add is_moderator role to users.

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("is_moderator", sa.Boolean(), nullable=False, server_default=sa.text("false"))
        )


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_column("is_moderator")
