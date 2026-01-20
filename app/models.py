from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="resident")  # resident | admin
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(password, self.password_hash)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="New")  # New/Reviewed/Approved/Rejected
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_headline = db.Column(db.String(500), nullable=True)
    home_subhead = db.Column(db.String(500), nullable=True)
    home_lead = db.Column(db.String(800), nullable=True)
    youtube_url = db.Column(db.String(800), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def ensure_default_settings():
    s = SiteSettings.query.first()
    if not s:
        s = SiteSettings(
            home_headline="A safe, sober place to live while you get back on your feet.",
            home_subhead="Transitional sober living for recovery & reentry — with structure, support, and a plan for what’s next.",
            home_lead="We focus on daily routines, peer support, and practical life skills. If someone needs medical or clinical treatment, we help connect them to licensed professionals.",
            youtube_url=""
        )
        db.session.add(s)
        db.session.commit()

def bootstrap_admin_if_configured():
    admin_email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
    admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        return
    existing = User.query.filter_by(email=admin_email.strip().lower()).first()
    if existing:
        if existing.role != "admin":
            existing.role = "admin"
            db.session.commit()
        return
    u = User(email=admin_email.strip().lower(), role="admin")
    u.set_password(admin_password)
    db.session.add(u)
    db.session.commit()
