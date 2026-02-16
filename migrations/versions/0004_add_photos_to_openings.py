
"""Add photos_json to openings.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"


def upgrade():
    with op.batch_alter_table("openings") as batch_op:
        batch_op.add_column(sa.Column("photos_json", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("openings") as batch_op:
        batch_op.drop_column("photos_json")
