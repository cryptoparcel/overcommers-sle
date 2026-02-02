from __future__ import annotations

import json
from flask import Blueprint, flash, redirect, render_template, url_for, send_from_directory, current_app, request, Response
from flask_login import current_user

from ..extensions import db, limiter
from ..utils import slugify
from ..utils.mailer import send_email
from ..forms import ApplyForm, ContactForm, StorySubmitForm
from ..models import Application, ContactMessage, Story, PageLayout, Opening

public_bp = Blueprint("public", __name__)

@public_bp.get("/favicon.ico")
def favicon():
    return send_from_directory(current_app.static_folder, "assets/favicon.ico")

@public_bp.get("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"
    return Response(body, mimetype="text/plain")

@public_bp.get("/sitemap.xml")
def sitemap():
    # Lightweight sitemap with priorities/changefreq
    # Note: <loc> should be absolute in perfect SEO, but relative works behind reverse proxies.
    pages = [
        ("/", "daily", "1.0"),
        ("/what-we-do", "monthly", "0.8"),
        ("/resources", "weekly", "0.7"),
        ("/impact", "monthly", "0.6"),
        ("/shop", "monthly", "0.5"),
        ("/contact", "weekly", "0.7"),
        ("/apply", "weekly", "0.8"),
        ("/stories", "weekly", "0.6"),
        ("/privacy", "yearly", "0.3"),
        ("/terms", "yearly", "0.3"),
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, pr in pages:
        xml.append("<url>")
        xml.append(f"  <loc>{loc}</loc>")
        xml.append(f"  <changefreq>{freq}</changefreq>")
        xml.append(f"  <priority>{pr}</priority>")
        xml.append("</url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")

@public_bp.get("/")
def index():
    layout = PageLayout.query.filter_by(page="home").first()
    blocks = None
    if layout and layout.layout_json:
        try:
            data = json.loads(layout.layout_json)
            blocks = data.get("blocks") if isinstance(data, dict) else None
        except Exception:
            blocks = None
    openings_preview = Opening.query.filter_by(status="published").order_by(Opening.created_at.desc()).limit(3).all()
    return render_template("index.html", title="Overcomers | SLE", page_blocks=blocks, openings_preview=openings_preview)

@public_bp.get("/what-we-do")
def what_we_do():
    return render_template("whatwedo.html", title="What We Do")

@public_bp.get("/resources")
def resources():
    return render_template("resources.html", title="Resources")

@public_bp.get("/impact")
def impact():
    return render_template("impact.html", title="Impact")

@public_bp.get("/shop")
def shop():
    return render_template("shop.html", title="Shop")

@public_bp.get("/contact")
def contact():
    form = ContactForm()
    return render_template("contact.html", form=form, title="Contact")

@public_bp.post("/contact")
@limiter.limit("10 per hour")
def contact_post():
    form = ContactForm()
    if not form.validate_on_submit():
        flash("Please check the form and try again.", "error")
        return render_template("contact.html", form=form, title="Contact"), 400

    msg = ContactMessage(
        name=form.name.data.strip(),
        email=form.email.data.strip().lower(),
        subject=form.subject.data.strip(),
        message=form.message.data.strip(),
    )
    db.session.add(msg)
    db.session.commit()

    body = (
        "New contact message\n\n"
        f"Name: {msg.name}\n"
        f"Email: {msg.email}\n"
        f"Subject: {msg.subject}\n\n"
        f"{msg.message}\n"
    )
    send_email(to_email=current_app.config.get("NOTIFY_EMAIL"), subject=f"[Overcomers] Contact: {msg.subject}", body=body)

    flash("Thanks — we got your message.", "success")
    return redirect(url_for("public.contact"))

@public_bp.get("/apply")
def apply():
    form = ApplyForm()
    return render_template("apply.html", form=form, title="Apply")

@public_bp.post("/apply")
@limiter.limit("10 per hour")
def apply_post():
    form = ApplyForm()
    if not form.validate_on_submit():
        flash("Please check the form and try again.", "error")
        return render_template("apply.html", form=form, title="Apply"), 400

    app_row = Application(
        full_name=form.full_name.data.strip(),
        email=form.email.data.strip().lower(),
        phone=(form.phone.data.strip() if form.phone.data else None),
        message=(form.message.data.strip() if form.message.data else None),
    )
    db.session.add(app_row)
    db.session.commit()

    body = (
        "New application\n\n"
        f"Name: {app_row.full_name}\n"
        f"Email: {app_row.email}\n"
        f"Phone: {app_row.phone or '-'}\n\n"
        f"Message:\n{app_row.message or '-'}\n"
    )
    send_email(to_email=current_app.config.get("NOTIFY_EMAIL"), subject="[Overcomers] New application", body=body)

    flash("Thanks — we’ll reach out soon.", "success")
    return redirect(url_for("public.apply"))

@public_bp.get("/privacy")
def privacy():
    return render_template("legal/privacy.html", title="Privacy Policy")

@public_bp.get("/terms")
def terms():
    return render_template("legal/terms.html", title="Terms of Use")

@public_bp.get("/stories")
def stories():
    items = Story.query.filter_by(status="approved").order_by(Story.created_at.desc()).limit(50).all()
    return render_template("stories.html", stories=items, title="Stories")

@public_bp.get("/stories/<slug>")
def story_detail(slug: str):
    story = Story.query.filter_by(slug=slug, status="approved").first_or_404()
    return render_template("story_detail.html", story=story, title=story.title)

@public_bp.route("/stories/submit", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def story_submit():
    form = StorySubmitForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = slugify(title)
        base = slug
        i = 2
        while Story.query.filter_by(slug=slug).first() is not None:
            slug = f"{base}-{i}"
            i += 1

        story = Story(
            title=title,
            slug=slug,
            summary=(form.summary.data or "").strip() or None,
            body=form.body.data.strip(),
            image_url=(form.image_url.data or "").strip() or None,
            author_name=(form.author_name.data or "").strip() or None,
            status="pending",
        )
        db.session.add(story)
        db.session.commit()

        admin_email = current_app.config.get("NOTIFY_EMAIL")
        if admin_email:
            send_email(
                to_email=admin_email,
                subject="New story submission (Overcomers SLE)",
                body=f"Title: {story.title}\nAuthor: {story.author_name or '(not provided)'}\n\nReview in /admin/stories",
            )
        flash("Thanks! Your story was submitted for review.", "success")
        return redirect(url_for("public.stories"))
    return render_template("story_submit.html", form=form, title="Share a story")

@public_bp.get("/careers")
def careers():
    return render_template("careers.html", title="Careers")

@public_bp.get("/checkout")
def checkout():
    return render_template("checkout.html", title="Checkout")


@public_bp.get("/openings")
def openings():
    items = (
        Opening.query.filter_by(status="published")
        .order_by(Opening.created_at.desc())
        .limit(100)
        .all()
    )
    return render_template("openings.html", openings=items, title="Upcoming Openings")


@public_bp.get("/openings/<slug>")
def opening_detail(slug: str):
    row = Opening.query.filter_by(slug=slug, status="published").first_or_404()
    return render_template("opening_detail.html", opening=row, title=row.title)
