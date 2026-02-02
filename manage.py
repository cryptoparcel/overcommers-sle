"""Small management CLI.

Usage:
  python manage.py make-admin you@example.com
  python manage.py bootstrap-db
"""

from __future__ import annotations

import click

from app import create_app
from app.extensions import db
from app.models import User
from app.seed import seed_defaults

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
            raise click.ClickException(f"No user found for {email}. Create the account first.")
        user.is_admin = True
        db.session.commit()
        click.echo(f"✅ {user.email} is now an admin")

@cli.command("bootstrap-db")
def bootstrap_db() -> None:
    """Create tables and seed default content."""
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_defaults()
        click.echo("✅ Database bootstrapped (tables created + defaults seeded).")

if __name__ == "__main__":
    cli()
