from __future__ import annotations
import os

def _normalize_database_url(url: str | None) -> str:
    if not url:
        return "sqlite:///local.db"
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

class Config:
    def __init__(self) -> None:
        # Core
        self.SECRET_KEY = os.environ.get("SECRET_KEY", "dev-not-secure-change-me")
        self.SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.environ.get("DATABASE_URL"))
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        # Safety: crash loudly if deployed with default secret
        if os.environ.get("RENDER") and self.SECRET_KEY == "dev-not-secure-change-me":
            raise RuntimeError(
                "SECRET_KEY is not set! Add it as an environment variable in Render."
            )

        # HTTPS
        self.PREFERRED_URL_SCHEME = "https" if os.environ.get("RENDER") else "http"

        # Cookies
        self.SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
        self.PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

        # Email notifications
        self.SMTP_HOST = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
        self.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
        self.SMTP_FROM = os.environ.get("SMTP_FROM", "") or self.SMTP_USERNAME or "no-reply@overcomersrc.com"
        self.NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "info@overcomersrc.com")

        # Optional reCAPTCHA (v2 checkbox)
        self.RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
        self.RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")

        # Auto-bootstrap admin from env (optional)
        self.ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
        self.ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
