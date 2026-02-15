
from __future__ import annotations

import os
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
    app.url_map.strict_slashes = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def _load_user(user_id: str):  # pragma: no cover
        try:
            return db.session.get(User, int(user_id))
        except Exception:
            return None

    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)

    register_cli(app)

    # ── Security headers ─────────────────────────────────────
    @app.after_request
    def _security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://plausible.io https://www.google.com https://www.gstatic.com https://www.paypal.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "frame-src https://www.paypal.com https://www.google.com; "
            "connect-src 'self' https://plausible.io https://www.google.com"
        )
        if os.environ.get("RENDER"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Cache static assets aggressively (CSS, JS, images)
        if response.content_type and any(t in response.content_type for t in ("css", "javascript", "image", "font")):
            response.headers["Cache-Control"] = "public, max-age=2592000"  # 30 days
        return response

    # ── Template filters ─────────────────────────────────────
    @app.template_filter("nl2br")
    def nl2br(s: str) -> str:
        if not s:
            return Markup("")
        from markupsafe import escape
        escaped = escape(s)
        return Markup(
            str(escaped)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\n", "<br>")
        )

    # ── Auto-bootstrap admin from env vars on first request ──
    _admin_bootstrapped = {"done": False}

    @app.before_request
    def _auto_bootstrap_admin():
        """Create admin user from ADMIN_EMAIL + ADMIN_PASSWORD env vars if no admin exists yet."""
        if _admin_bootstrapped["done"]:
            return
        _admin_bootstrapped["done"] = True

        admin_email = app.config.get("ADMIN_EMAIL", "").strip().lower()
        admin_password = app.config.get("ADMIN_PASSWORD", "").strip()
        if not admin_email or not admin_password:
            return
        try:
            existing = User.query.filter_by(email=admin_email).first()
            if existing:
                if not existing.is_admin:
                    existing.is_admin = True
                    existing.email_confirmed = True
                    db.session.commit()
                    app.logger.info(f"Promoted {admin_email} to admin via env vars.")
                return
            user = User(
                name="Admin",
                email=admin_email,
                username=admin_email.split("@")[0],
                email_confirmed=True,
            )
            user.set_password(admin_password)
            user.is_admin = True
            db.session.add(user)
            db.session.commit()
            app.logger.info(f"Auto-created admin user: {admin_email}")
        except Exception as e:
            app.logger.warning(f"Admin bootstrap skipped: {e}")

    return app
