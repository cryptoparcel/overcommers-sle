
"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- applications ---
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'new'")),
    )
    op.create_index("ix_applications_email", "applications", ["email"], unique=False)

    # --- contact messages ---
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
    )

    # --- stories ---
    op.create_table(
        "stories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("summary", sa.String(length=320), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("author_name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_stories_slug", "stories", ["slug"], unique=True)

    # --- page layouts ---
    op.create_table(
        "page_layouts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("page", sa.String(length=64), nullable=False),
        sa.Column("layout_json", sa.Text(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_page_layouts_page", "page_layouts", ["page"], unique=True)

    # --- openings ---
    op.create_table(
        "openings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=64), nullable=True, server_default=sa.text("'CA'")),
        sa.Column("beds_available", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("available_on", sa.Date(), nullable=True),
        sa.Column("price_monthly", sa.String(length=60), nullable=True, server_default=sa.text("'$1,000 / month'")),
        sa.Column("deposit", sa.String(length=60), nullable=True, server_default=sa.text("'$1,000 deposit'")),
        sa.Column("hide_price", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("summary", sa.String(length=320), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("house_rules", sa.Text(), nullable=True),
        sa.Column("included", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.String(length=120), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=60), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'draft'")),
    )
    op.create_index("ix_openings_slug", "openings", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_openings_slug", table_name="openings")
    op.drop_table("openings")
    op.drop_index("ix_page_layouts_page", table_name="page_layouts")
    op.drop_table("page_layouts")
    op.drop_index("ix_stories_slug", table_name="stories")
    op.drop_table("stories")
    op.drop_table("contact_messages")
    op.drop_index("ix_applications_email", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
