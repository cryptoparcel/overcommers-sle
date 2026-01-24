from __future__ import annotations

import os


def _normalize_database_url(url: str | None) -> str:
    """Render often provides URLs like postgresql://...
    SQLAlchemy with psycopg expects postgresql+psycopg://...
    """
    if not url:
        return "sqlite:///local.db"
    url = url.strip()

    # Render sometimes uses 'postgres://' in older setups
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    # Add driver for psycopg (v3) if not specified
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url


class Config:
    """Config is loaded from environment variables in Render."""

    def __init__(self) -> None:
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

        self.SQLALCHEMY_DATABASE_URI = _normalize_database_url(
            os.environ.get("DATABASE_URL")
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        # Flask-Login
        self.LOGIN_VIEW = "auth.login"
        self.LOGIN_MESSAGE_CATEGORY = "info"

        # Rate limiting (Flask-Limiter)
        self.RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "200 per day;60 per hour")
        self.RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

        # Security / cookies
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")

        # Render terminates TLS and forwards HTTPS; secure cookies are recommended.
        # Locally, set SESSION_COOKIE_SECURE=0 if you run http://
        self.SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") == "1"

        # Email notifications (optional)
        self.SMTP_HOST = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
        self.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
        self.SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1") == "1"
        self.FROM_EMAIL = os.environ.get("FROM_EMAIL", "no-reply@overcomerssle.com")
        self.NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "info@overcomerssle.com")

