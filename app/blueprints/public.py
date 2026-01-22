from flask import Blueprint, render_template, request
from ..models import SiteSettings, Application, Page
from .. import db
from .. import limiter
import re
import os
import requests
from markdown import markdown

public_bp = Blueprint("public", __name__)

def youtube_to_embed(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if "youtube.com/embed/" in url:
        return url
    m = re.search(r"youtu\.be/([\w-]+)", url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    m = re.search(r"v=([\w-]+)", url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    m = re.search(r"youtube\.com/shorts/([\w-]+)", url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    return url

@public_bp.get("/")
def index():
    s = SiteSettings.query.first()
    embed = youtube_to_embed(s.youtube_url if s else "")
    return render_template(
        "index.html",
        title="OVERCOMERS | SLE — Transitional Sober Living",
        home_headline=(s.home_headline if s else None),
        home_subhead=(s.home_subhead if s else None),
        home_lead=(s.home_lead if s else None),
        youtube_embed_url=embed,
        hero_image_url=(s.hero_image_url if s else None)
    )

@public_bp.route("/apply", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def apply():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        message = (request.form.get("message") or "").strip()
        token = request.form.get("cf-turnstile-response") or ""
        if not verify_turnstile(token, request.remote_addr or ""):
            return render_template("apply.html", title="Apply — OVERCOMERS | SLE", error="Please verify you’re human and try again.", turnstile_site_key=os.environ.get("TURNSTILE_SITE_KEY",""))
        if not name or not email or not phone:
            return render_template("apply.html", title="Apply — OVERCOMERS | SLE", error="Please fill name, email, and phone.")
        a = Application(name=name, email=email, phone=phone, message=message)
        db.session.add(a)
        db.session.commit()

        admin_notify = os.environ.get("ADMIN_NOTIFY_EMAIL", "")
        subject = "New application received"
        body = f"New application:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}\n"
        if admin_notify:
            send_email(subject, body, admin_notify)
        send_email("We received your application", "Thanks for reaching out. We received your application and will follow up soon.", email)

        return render_template("apply.html", title="Apply — OVERCOMERS | SLE", success="Thanks — your application was submitted.", turnstile_site_key=os.environ.get("TURNSTILE_SITE_KEY",""))
    return render_template("apply.html", title="Apply — OVERCOMERS | SLE", turnstile_site_key=os.environ.get("TURNSTILE_SITE_KEY",""))

@public_bp.get("/what-we-do")
def what_we_do():
    p = Page.query.filter_by(slug="what-we-do").first()
    title = (p.title if p else "What We Do")
    html = markdown(p.body_md) if p else ""
    return render_template("what_we_do.html", title=f"{title} — OVERCOMERS | SLE", page_title=title, page_html=html)

@public_bp.get("/resources")
def resources():
    p = Page.query.filter_by(slug="resources").first()
    title = (p.title if p else "Resources")
    html = markdown(p.body_md) if p else ""
    return render_template("resources.html", title=f"{title} — OVERCOMERS | SLE", page_title=title, page_html=html)

@public_bp.get("/impact")
def impact():
    p = Page.query.filter_by(slug="impact").first()
    title = (p.title if p else "Impact")
    html = markdown(p.body_md) if p else ""
    return render_template("impact.html", title=f"{title} — OVERCOMERS | SLE", page_title=title, page_html=html)

@public_bp.get("/shop")
def shop():
    return render_template("shop.html", title="Shop — OVERCOMERS | SLE")

@public_bp.get("/contact")
def contact():
    p = Page.query.filter_by(slug="contact").first()
    title = (p.title if p else "Contact")
    html = markdown(p.body_md) if p else ""
    return render_template("contact.html", title=f"{title} — OVERCOMERS | SLE", page_title=title, page_html=html)

@public_bp.get("/careers")
def careers():
    p = Page.query.filter_by(slug="careers").first()
    title = (p.title if p else "Careers")
    html = markdown(p.body_md) if p else ""
    return render_template("careers.html", title=f"{title} — OVERCOMERS | SLE", page_title=title, page_html=html)

@public_bp.get("/privacy")
def privacy():
    return render_template("privacy.html", title="Privacy — OVERCOMERS | SLE")

@public_bp.get("/terms")
def terms():
    return render_template("terms.html", title="Terms — OVERCOMERS | SLE")


def verify_turnstile(token: str, remoteip: str) -> bool:
    secret = os.environ.get("TURNSTILE_SECRET_KEY", "")
    if not secret:
        return True
    if not token:
        return False
    try:
        resp = requests.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={"secret": secret, "response": token, "remoteip": remoteip},
            timeout=6,
        )
        data = resp.json()
        return bool(data.get("success"))
    except Exception:
        return False

def send_email(subject: str, body: str, to_email: str) -> None:
    host = os.environ.get("SMTP_HOST", "")
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("SMTP_FROM", user or "no-reply@overcomerssle.com")
    port = int(os.environ.get("SMTP_PORT", "587") or 587)
    if not host or not user or not password:
        return

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as s:
        s.starttls()
        s.login(user, password)
        s.send_message(msg)


@public_bp.get("/health")
def health():
    return {"status": "ok"}
