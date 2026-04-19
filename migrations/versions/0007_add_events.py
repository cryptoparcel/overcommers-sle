"""Add events table for community events page.

Revision ID: 0007
Revises: 0006
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"


def upgrade():
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False, unique=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.String(30), nullable=True),
        sa.Column("end_time", sa.String(30), nullable=True),
        sa.Column("location_name", sa.String(180), nullable=True),
        sa.Column("location_address", sa.String(255), nullable=True),
        sa.Column("summary", sa.String(320), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(40), nullable=True, server_default="general"),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("allow_rsvp", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rsvp_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_events_start_date", "events", ["start_date"])
    op.create_index("ix_events_slug", "events", ["slug"], unique=True)


def downgrade():
    op.drop_index("ix_events_slug", "events")
    op.drop_index("ix_events_start_date", "events")
    op.drop_table("events")
