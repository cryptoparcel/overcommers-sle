"""Add activity_logs table for audit trail.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("action", sa.String(80), nullable=False, index=True),
        sa.Column("category", sa.String(30), nullable=False, default="general", index=True),
        sa.Column("path", sa.String(500), nullable=True),
        sa.Column("method", sa.String(10), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("resource_type", sa.String(60), nullable=True),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(10), nullable=False, default="info"),
    )


def downgrade():
    op.drop_table("activity_logs")
