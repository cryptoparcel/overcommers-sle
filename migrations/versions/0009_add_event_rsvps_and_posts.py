"""Add event_rsvps and event_posts tables for the event thread feature.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"


def upgrade():
    op.create_table(
        "event_rsvps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_rsvp_user"),
    )
    op.create_index("ix_event_rsvps_event_id", "event_rsvps", ["event_id"])
    op.create_index("ix_event_rsvps_user_id", "event_rsvps", ["user_id"])

    op.create_table(
        "event_posts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_event_posts_event_id", "event_posts", ["event_id"])
    op.create_index("ix_event_posts_user_id", "event_posts", ["user_id"])
    op.create_index("ix_event_posts_created_at", "event_posts", ["created_at"])


def downgrade():
    op.drop_index("ix_event_posts_created_at", "event_posts")
    op.drop_index("ix_event_posts_user_id", "event_posts")
    op.drop_index("ix_event_posts_event_id", "event_posts")
    op.drop_table("event_posts")

    op.drop_index("ix_event_rsvps_user_id", "event_rsvps")
    op.drop_index("ix_event_rsvps_event_id", "event_rsvps")
    op.drop_table("event_rsvps")
