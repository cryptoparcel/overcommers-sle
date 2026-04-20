"""Add password reset token fields to users.

Revision ID: 0011
Revises: 0010
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("reset_token", sa.String(64), nullable=True))
        batch.add_column(sa.Column("reset_token_expires", sa.DateTime(), nullable=True))
        batch.create_index("ix_users_reset_token", ["reset_token"], unique=True)


def downgrade():
    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_reset_token")
        batch.drop_column("reset_token_expires")
        batch.drop_column("reset_token")
