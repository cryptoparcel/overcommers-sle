
"""OVERCOMERS management CLI.

This project intentionally has **no** "make yourself admin" button.
Admins are created via a command.

Works locally and on Render (open the Shell for your web service).

Examples:
  python manage.py make-admin you@example.com
  python manage.py run

Flask CLI alternatives (also supported):
  flask --app wsgi:app make-admin you@example.com
  flask --app wsgi:app bootstrap-db
"""

from __future__ import annotations

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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


@cli.command("run")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=5000, show_default=True, type=int)
@click.option("--debug/--no-debug", default=True, show_default=True)
def run_server(host: str, port: int, debug: bool) -> None:
    """Run the dev server (convenience wrapper)."""

    app = create_app()
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    cli()
