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
"privacy": ("Privacy Policy", "## Privacy Policy (California-focused)\n\n**Effective date:** 2026-01-22\n\nThis policy explains how we collect, use, and share information when you use our website. We aim to use only what we need, protect it, and keep things simple.\n\n### What we collect\n- **Contact info** (name, email, phone if you choose)\n- **Account info** (username, login data, security logs)\n- **Application info** you submit (for housing inquiries)\n- **Technical info** (IP address, device/browser, approximate location, basic analytics)\n\n### Why we collect it\n- To respond to applications and messages\n- To operate and secure the site (prevent spam and abuse)\n- To improve the user experience\n\n### How we share it\nWe do **not** sell personal information. We may share limited information with service providers (hosting, email delivery, security) strictly to run the website.\n\n### Cookies\nWe use essential cookies for login and security. You can block cookies, but parts of the site may not work.\n\n### Your California privacy rights\nIf we are a “business” covered by California’s privacy laws (CCPA/CPRA), you may have rights such as:\n- **Right to know/access** what we collect\n- **Right to delete** certain information\n- **Right to correct** inaccurate information\n- **Right to opt out of sale/sharing** (we do not sell; if that ever changes, we will provide an opt-out)\n\nTo request access, deletion, or correction, email **info@overcomerssle.com** with the subject **“Privacy Request.”**\n\n### Security\nNo website can guarantee perfect security, but we use reasonable safeguards and limit access.\n\n### Children\nThis site is intended for general audiences. If you believe a child provided personal info, contact us and we will remove it.\n\n### Updates\nWe may update this policy. We will change the effective date above when we do."),
"terms": ("Terms of Service", "## Terms of Service\n\n**Effective date:** 2026-01-22\n\nBy using this website, you agree to these terms.\n\n### Not medical or legal advice\nInformation on this website is for **general informational purposes** only and is **not** medical, therapeutic, legal, or professional advice. Always seek qualified professionals for your specific situation.\n\n### No guarantees\nPrograms, resources, and information do **not** guarantee outcomes (housing acceptance, sobriety, employment, legal results, or any other outcome).\n\n### Supportive housing notice\nWe provide supportive, peer-based sober living. We do **not** provide detox, clinical treatment, or therapy services. We may refer you to licensed providers if needed.\n\n### Shop terms\nMerchandise purchases:\n- Are **not** donations\n- Do **not** guarantee services or outcomes\n- Are provided “as-is” unless stated otherwise\n\n### Acceptable use\nDo not misuse the site, attempt unauthorized access, or submit false or harmful content.\n\n### Limitation of liability\nTo the fullest extent permitted by law, we are not liable for indirect or consequential damages arising from your use of the site. **Nothing in these terms limits liability where prohibited by law** (for example, liability for fraud, willful injury, or violations of law).\n\n### Changes\nWe may update these terms. Continued use of the site after updates means you accept the revised terms.\n\n### Contact\nQuestions: **info@overcomerssle.com**"),
    }
    for slug, (title, body) in defaults.items():
        if not Page.query.filter_by(slug=slug).first():
            db.session.add(Page(slug=slug, title=title, body_md=body))
    db.session.commit()
