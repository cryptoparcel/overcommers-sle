from flask import Blueprint, render_template, request
from ..models import SiteSettings, Application
from .. import db
import re

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
        youtube_embed_url=embed
    )

@public_bp.route("/apply", methods=["GET", "POST"])
def apply():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        message = (request.form.get("message") or "").strip()
        if not name or not email or not phone:
            return render_template("apply.html", title="Apply — OVERCOMERS | SLE", error="Please fill name, email, and phone.")
        a = Application(name=name, email=email, phone=phone, message=message)
        db.session.add(a)
        db.session.commit()
        return render_template("apply.html", title="Apply — OVERCOMERS | SLE", success="Thanks — your application was submitted.")
    return render_template("apply.html", title="Apply — OVERCOMERS | SLE")

@public_bp.get("/what-we-do")
def what_we_do():
    return render_template("what_we_do.html", title="What We Do — OVERCOMERS | SLE")

@public_bp.get("/resources")
def resources():
    return render_template("resources.html", title="Resources — OVERCOMERS | SLE")

@public_bp.get("/impact")
def impact():
    return render_template("impact.html", title="Impact — OVERCOMERS | SLE")

@public_bp.get("/shop")
def shop():
    return render_template("shop.html", title="Shop — OVERCOMERS | SLE")

@public_bp.get("/contact")
def contact():
    return render_template("contact.html", title="Contact — OVERCOMERS | SLE")

@public_bp.get("/careers")
def careers():
    return render_template("careers.html", title="Careers — OVERCOMERS | SLE")

@public_bp.get("/privacy")
def privacy():
    return render_template("privacy.html", title="Privacy — OVERCOMERS | SLE")

@public_bp.get("/terms")
def terms():
    return render_template("terms.html", title="Terms — OVERCOMERS | SLE")
