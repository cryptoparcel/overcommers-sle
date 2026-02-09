"""Add tour_requests, interest_signups tables and last_login column.

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade():
    # Add last_login to users
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("last_login", sa.DateTime(), nullable=True))

    # Create tour_requests table
    op.create_table(
        "tour_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("preferred_time", sa.String(200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # Create interest_signups table
    op.create_table(
        "interest_signups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("email", sa.String(255), nullable=False),
    )


def downgrade():
    op.drop_table("interest_signups")
    op.drop_table("tour_requests")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("last_login")
