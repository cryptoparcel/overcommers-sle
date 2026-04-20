"""Add edited_at to event_posts and opening_posts.

Revision ID: 0013
Revises: 0012
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"


def upgrade():
    with op.batch_alter_table("event_posts") as batch:
        batch.add_column(sa.Column("edited_at", sa.DateTime(), nullable=True))
    with op.batch_alter_table("opening_posts") as batch:
        batch.add_column(sa.Column("edited_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("opening_posts") as batch:
        batch.drop_column("edited_at")
    with op.batch_alter_table("event_posts") as batch:
        batch.drop_column("edited_at")
