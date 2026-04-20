"""Add opening_posts table for the opening discussion thread feature.

Revision ID: 0010
Revises: 0009
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"


def upgrade():
    op.create_table(
        "opening_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("opening_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["opening_id"], ["openings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_opening_posts_opening_id", "opening_posts", ["opening_id"])
    op.create_index("ix_opening_posts_user_id", "opening_posts", ["user_id"])
    op.create_index("ix_opening_posts_created_at", "opening_posts", ["created_at"])


def downgrade():
    op.drop_index("ix_opening_posts_created_at", "opening_posts")
    op.drop_index("ix_opening_posts_user_id", "opening_posts")
    op.drop_index("ix_opening_posts_opening_id", "opening_posts")
    op.drop_table("opening_posts")
