from app import create_app

# Ensure custom CLI commands are available even when the app is loaded as
# an already-instantiated object (e.g. `--app wsgi:app`).
from app.cli import register_cli

app = create_app()
register_cli(app)
