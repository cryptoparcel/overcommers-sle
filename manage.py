"""Small management CLI.

Why this exists:
Some hosting shells make it awkward to load Flask's `flask` CLI with app
factories. This script gives you a guaranteed way to run admin tasks.

Usage:
  python manage.py make-admin you@example.com
"""

from __future__ import annotations

import click

from app import create_app
from app.extensions import db
from app.models import User


@click.group()
def cli() -> None:
    """Management commands."""


@cli.command("make-admin")
@click.argument("email")
def make_admin(email: str) -> None:
    """Promote an existing user to admin by email."""

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            raise click.ClickException(f"No user found for {email}")
        user.is_admin = True
        db.session.commit()
        click.echo(f"{user.email} is now an admin")


if __name__ == "__main__":
    cli()
