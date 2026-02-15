
"""Add email confirmation to users, unique constraint on interest_signups.email.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade():
    # Email confirmation columns on users
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("0")))
        batch_op.add_column(sa.Column("confirm_token", sa.String(64), nullable=True))
        batch_op.create_index("ix_users_confirm_token", ["confirm_token"], unique=True)

    # Unique constraint + index on interest_signups.email
    with op.batch_alter_table("interest_signups") as batch_op:
        batch_op.create_index("ix_interest_signups_email", ["email"], unique=True)

    # Auto-confirm any existing users (they registered before this feature)
    op.execute("UPDATE users SET email_confirmed = 1")


def downgrade():
    with op.batch_alter_table("interest_signups") as batch_op:
        batch_op.drop_index("ix_interest_signups_email")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_confirm_token")
        batch_op.drop_column("confirm_token")
        batch_op.drop_column("email_confirmed")
