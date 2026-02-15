
from __future__ import annotations

from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

def _utcnow():
    return datetime.now(timezone.utc)
from flask_login import UserMixin

from .extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Email confirmation
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    confirm_token = db.Column(db.String(64), unique=True, nullable=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=True)

    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default="new", nullable=False, index=True)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)


class TourRequest(db.Model):
    """Tour request submissions from /tour."""
    __tablename__ = "tour_requests"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40), nullable=True)
    preferred_time = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)


class InterestSignup(db.Model):
    """Email interest list when no openings are posted."""
    __tablename__ = "interest_signups"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)


class Story(db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), unique=True, index=True, nullable=False)
    summary = db.Column(db.String(320), nullable=True)
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    author_name = db.Column(db.String(120), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending", index=True)  # pending | approved | rejected
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class PageLayout(db.Model):
    __tablename__ = "page_layouts"

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(64), unique=True, nullable=False, index=True)
    layout_json = db.Column(db.Text, nullable=False, default="{}")
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


class Opening(db.Model):
    """A published listing for available beds/rooms."""

    __tablename__ = "openings"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), unique=True, index=True, nullable=False)

    city = db.Column(db.String(120), nullable=True, default="Grover Beach")
    state = db.Column(db.String(64), nullable=True, default="CA")

    beds_available = db.Column(db.Integer, nullable=False, default=1)
    available_on = db.Column(db.Date, nullable=True)

    price_monthly = db.Column(db.String(60), nullable=True, default="$1,000 / month")
    deposit = db.Column(db.String(60), nullable=True, default="$1,000 deposit")
    hide_price = db.Column(db.Boolean, nullable=False, default=True)

    summary = db.Column(db.String(320), nullable=True)
    details = db.Column(db.Text, nullable=True)
    house_rules = db.Column(db.Text, nullable=True)
    included = db.Column(db.Text, nullable=True)

    contact_name = db.Column(db.String(120), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(60), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="draft", index=True)

    def __repr__(self) -> str:
        return f"<Opening {self.id} {self.status} {self.slug}>"
