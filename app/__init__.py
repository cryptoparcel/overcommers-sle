from __future__ import annotations

import os
from flask import Flask

from .extensions import db, login_manager, limiter, csrf
from . import login  # noqa: F401
from .config import Config
from .blueprints.public import public_bp
from .blueprints.auth import auth_bp
from .blueprints.errors import errors_bp


def create_app() -> Flask:
    """Application factory for Overcomers SLE."""
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration
    app.config.from_object(Config())

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(errors_bp)

    # Create tables (simple bootstrap; for production prefer migrations)
    with app.app_context():
        db.create_all()

    return app
