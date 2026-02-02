from __future__ import annotations

import click
from flask import Flask
from .extensions import db
from .models import User
from .seed import seed_content

@click.command("make-admin")
@click.argument("email")
def make_admin(email: str) -> None:
    user = User.query.filter_by(email=email.lower().strip()).first()
    if not user:
        raise click.ClickException("No user found with that email. Create the account first, then rerun.")
    user.is_admin = True
    db.session.commit()
    click.echo(f"✅ {user.email} is now an admin")

@click.command("bootstrap-db")
def bootstrap_db() -> None:
    db.create_all()
    seed_content()
    click.echo("✅ Database bootstrapped (tables created + defaults seeded).")

def register_cli(app: Flask) -> None:
    app.cli.add_command(make_admin)
    app.cli.add_command(bootstrap_db)
