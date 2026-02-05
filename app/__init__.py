from __future__ import annotations

from flask import Flask
from markupsafe import Markup
from .config import Config
from .extensions import db, login_manager, limiter, csrf, migrate
from .blueprints.public import public_bp
from .blueprints.auth import auth_bp
from .blueprints.admin import admin_bp
from .blueprints.errors import errors_bp
from .cli import register_cli

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Flask-Login: load a user from the session
    from .models import User

    @login_manager.user_loader
    def _load_user(user_id: str):  # pragma: no cover
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None
    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)

    register_cli(app)

    @app.template_filter("nl2br")
    def nl2br(s: str) -> str:
        if not s:
            return ""
        return (str(s).replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>"))


    return app
