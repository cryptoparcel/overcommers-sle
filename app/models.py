from __future__ import annotations

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Flask-Login integration
    @property
    def is_authenticated(self) -> bool:  # pragma: no cover
        return True

    @property
    def is_active(self) -> bool:  # pragma: no cover
        return True

    @property
    def is_anonymous(self) -> bool:  # pragma: no cover
        return False

    def get_id(self) -> str:  # pragma: no cover
        return str(self.id)


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(40), nullable=True)

    message = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(32), default="new", nullable=False)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)


class Story(db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), unique=True, index=True, nullable=False)
    summary = db.Column(db.String(320), nullable=True)
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    author_name = db.Column(db.String(120), nullable=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending | approved | rejected
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Story {self.id} {self.status} {self.slug}>"


class PageLayout(db.Model):
    """Stores a simple draggable layout JSON for a given page key (e.g. 'home').

    The admin "Page Builder" saves JSON that the public site can render into
    positioned blocks.
    """

    __tablename__ = "page_layouts"

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(64), unique=True, nullable=False, index=True)
    layout_json = db.Column(db.Text, nullable=False, default="{}")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<PageLayout {self.page}>"
