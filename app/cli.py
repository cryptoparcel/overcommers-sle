"""Custom Flask CLI commands.

We register these commands explicitly so they're available in environments
like Render where you may run `flask --app wsgi:app ...` in a shell.
"""

from __future__ import annotations

import click
from flask import Flask

from .extensions import db
from .models import User


@click.command("make-admin")
@click.argument("email")
def make_admin(email: str) -> None:
    """Promote an existing user to admin by email."""
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        raise click.ClickException(
            "No user found with that email. Create the account first, then rerun."
        )
    user.is_admin = True
    db.session.commit()
    click.echo(f"✅ {user.email} is now an admin")


def register_cli(app: Flask) -> None:
    """Register CLI commands on a Flask app."""
    app.cli.add_command(make_admin)
