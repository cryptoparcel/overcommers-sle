
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
        """Load a user from a versioned ID like "42:3".

        The version after the colon is User.session_version — if the user
        has bumped it (e.g. "sign out of other sessions" or admin-locked),
        the cookie's version no longer matches and we return None, which
        logs the session out.
        """
        try:
            raw = str(user_id)
            uid_part, _, ver_part = raw.partition(":")
            uid = int(uid_part)
            expected_version = int(ver_part) if ver_part else 0
            user = db.session.get(User, uid)
            if not user:
                return None
            if user.is_locked:
                return None
            if (user.session_version or 0) != expected_version:
                return None
            return user
        except Exception:
            return None

    csrf.init_app(app)
    limiter.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)

    register_cli(app)

    # ── Activity logging middleware ──────────────────────────
    @app.after_request
    def _log_activity(response):
        """Log page views and form submissions for audit trail."""
        from flask import request as req
        # Skip static files, health checks, and API endpoints
        path = req.path or ""
        if any(path.startswith(p) for p in ("/static/", "/favicon", "/robots", "/health", "/manifest", "/sitemap")):
            return response
        # Skip AJAX/API and redirects (to avoid double-logging)
        if req.is_json or response.status_code in (301, 302, 304):
            return response

        try:
            from .utils import log_activity
            if req.method == "POST":
                # Log form submissions
                action = f"form_submit:{path}"
                log_activity(action=action, category="form_submit", level="info")
            elif req.method == "GET" and response.status_code == 200:
                # Log page views (sample: only log unique paths per session to reduce volume)
                action = f"page_view:{path}"
                log_activity(action=action, category="page_view", level="info")
        except Exception:
            pass  # Never break the app for logging
        return response

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
            "script-src 'self' 'unsafe-inline' https://plausible.io https://www.google.com https://www.gstatic.com https://www.paypal.com https://www.googletagmanager.com https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob: https:; "
            "frame-src https://www.paypal.com https://www.google.com https://js.stripe.com https://checkout.stripe.com; "
            "connect-src 'self' https://plausible.io https://www.google.com https://www.google-analytics.com https://api.stripe.com"
        )
        if os.environ.get("RENDER"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Cache static assets aggressively (CSS, JS, images)
        if response.content_type and any(t in response.content_type for t in ("css", "javascript", "image", "font")):
            response.headers["Cache-Control"] = "public, max-age=2592000"  # 30 days
        return response

    # ── Template filters ─────────────────────────────────────
    @app.context_processor
    def _inject_site_info():
        """Make site contact info available in all templates as {{ site.phone_display }} etc."""
        return {
            "site": {
                "phone_display": app.config.get("SITE_PHONE_DISPLAY", ""),
                "phone_tel": app.config.get("SITE_PHONE_TEL", ""),
                "email_support": app.config.get("SITE_EMAIL_SUPPORT", ""),
                "email_careers": app.config.get("SITE_EMAIL_CAREERS", ""),
                "email_billing": app.config.get("SITE_EMAIL_BILLING", ""),
                "email_legal": app.config.get("SITE_EMAIL_LEGAL", ""),
                "email_marketing": app.config.get("SITE_EMAIL_MARKETING", ""),
                "address_street": app.config.get("SITE_ADDRESS_STREET", ""),
                "address_city": app.config.get("SITE_ADDRESS_CITY", ""),
                "address_state": app.config.get("SITE_ADDRESS_STATE", ""),
                "address_zip": app.config.get("SITE_ADDRESS_ZIP", ""),
            }
        }

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

    # ── Schema bootstrap: create tables on first request if missing ──
    # Covers the case where build-time `flask db upgrade` failed (e.g. stale
    # DATABASE_URL during a Blueprint sync) but the live connection works.
    _schema_bootstrapped = {"done": False}

    @app.before_request
    def _auto_bootstrap_schema():
        if _schema_bootstrapped["done"]:
            return
        _schema_bootstrapped["done"] = True
        # First, try a proper alembic upgrade — handles both new tables and
        # column additions on existing tables (e.g. users.is_moderator).
        try:
            from flask_migrate import upgrade
            upgrade()
            app.logger.info("Alembic upgrade applied on first request.")
            return
        except Exception as e:
            app.logger.warning(f"Alembic upgrade on first request failed: {e}")
        # Fallback: if the DB is empty, create_all brings up all tables and
        # stamps alembic so future migrations apply cleanly.
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):
                app.logger.warning("Schema missing — running db.create_all() fallback.")
                db.create_all()
                try:
                    from flask_migrate import stamp
                    stamp(revision="head")
                    app.logger.info("Stamped alembic to head after create_all.")
                except Exception as e:
                    app.logger.warning(f"Alembic stamp skipped: {e}")
        except Exception as e:
            app.logger.error(f"Schema bootstrap fallback failed: {e}")

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
