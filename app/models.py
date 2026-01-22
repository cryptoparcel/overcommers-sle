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
    hero_image_url = db.Column(db.String(800), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def ensure_default_settings():
    s = SiteSettings.query.first()
    if not s:
        s = SiteSettings(
            home_headline="A safe, sober place to live while you get back on your feet.",
            home_subhead="Transitional sober living for recovery & reentry — with structure, support, and a plan for what’s next.",
            home_lead="We focus on daily routines, peer support, and practical life skills. If someone needs medical or clinical treatment, we help connect them to licensed professionals.",
            youtube_url="",
            hero_image_url=""
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


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    body_md = db.Column(db.Text, nullable=False, default="")
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

def ensure_default_pages():
    defaults = {
        "what-we-do": ("What We Do", "## What we do\n\nWe provide a structured, sober living environment with clear expectations and a supportive community.\n\n### What residents can expect\n- A drug- and alcohol-free home\n- House rules and routines\n- Peer support and accountability\n- Help connecting to jobs, IDs, and services\n\n> We do not provide medical, therapeutic, or detox services. We can connect you to licensed professionals if needed.\n"),
        "resources": ("Resources", "## Resources\n\nA simple list of helpful links and guides.\n\n- Recovery support groups\n- Reentry services\n- Job training\n- Housing and benefits\n"),
        "impact": ("Impact", "## Why it matters\n\nStable housing, routines, and support can reduce relapse and recidivism.\n\n### What we track\n- Housing stability\n- Job placement\n- Program completion\n"),
        "careers": ("Careers", "## Careers\n\nWe’re building a team that leads with empathy, structure, and accountability.\n\nEmail: info@overcomerssle.com\n"),
"privacy": ("Privacy Policy", "## Privacy Policy (California-focused)\n\n**Effective date:** 2026-01-22\n\nThis policy explains how we collect, use, and share information when you use our website.\n\n### Information we collect\n- **Contact info** (name, email, phone if you choose)\n- **Account info** (username, login security data)\n- **Application details** you submit through our forms\n- **Technical data** (IP address, device/browser info)\n\n### Why we collect it\n- To respond to messages and applications\n- To run the site safely (security, fraud prevention)\n- To improve the website experience\n\n### Sharing\nWe do **not** sell your personal information. We may share information with service providers (hosting, email delivery) only to operate the site.\n\n### Your California privacy rights\nDepending on whether we are a covered business under California privacy law, you may have rights such as **access/know**, **delete**, **correct**, and **opt out of sale or sharing**.\n\nTo request changes or ask questions, email **info@overcomerssle.com** with the subject line **\"Privacy Request\"**.\n\n### Cookies\nWe use essential cookies for login and security.\n\n### Changes\nWe may update this policy. The effective date will be updated above.\n"),
"terms": ("Terms of Service", "## Terms of Service\n\n**Effective date:** 2026-01-22\n\nBy using this website, you agree to these terms.\n\n### No medical, legal, or professional advice\nContent on this site is for **general informational purposes** and is **not** medical, therapeutic, legal, or professional advice. Always seek qualified professionals for your situation.\n\n### No guarantees\nProgram participation, resources, and information do not guarantee outcomes.\n\n### Supportive housing notice\nWe provide supportive, peer-based sober living. We do not provide detox, clinical treatment, or therapy services.\n\n### Shop terms\nIf you purchase merchandise, products are provided \"as-is\" unless stated otherwise. Purchases are not donations and do not guarantee services or outcomes.\n\n### Limitation of liability\nTo the fullest extent permitted by law, we are not liable for indirect damages arising from use of the site.\n\n### Contact\nQuestions: **info@overcomerssle.com**\n")

        "contact": ("Contact", "## Contact\n\nEmail: info@overcomerssle.com\n\nPhone: (408) 123-4567\nGeneral: (805) 202-8473\n\nLumpia Bros Cafe (ownership entity):\n1187 W Grand Ave, Grover Beach, CA 93433\n"),
    }
    for slug, (title, body) in defaults.items():
        if not Page.query.filter_by(slug=slug).first():
            db.session.add(Page(slug=slug, title=title, body_md=body))
    db.session.commit()
