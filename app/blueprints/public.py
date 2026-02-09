from __future__ import annotations

import json
from sqlalchemy import text
from flask import Blueprint, flash, redirect, render_template, url_for, send_from_directory, current_app, request, Response
from flask_login import current_user

from ..extensions import db, limiter
from ..utils import slugify
from ..utils.mailer import send_email
from ..forms import ApplyForm, ContactForm, StorySubmitForm, TourRequestForm, InterestForm
from ..models import Application, ContactMessage, Story, PageLayout, Opening, TourRequest, InterestSignup

public_bp = Blueprint("public", __name__)


# ── Static / SEO ─────────────────────────────────────────────

@public_bp.get("/favicon.ico")
def favicon():
    return send_from_directory(current_app.static_folder, "assets/favicon.ico")


@public_bp.get("/robots.txt")
def robots():
    body = "User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@public_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return Response(
        json.dumps({"status": "ok" if db_ok else "degraded", "db": db_ok}),
        status=status,
        mimetype="application/json",
    )


@public_bp.get("/sitemap.xml")
def sitemap():
    pages = [
        ("/", "daily", "1.0"),
        ("/guide", "monthly", "0.9"),
        ("/what-we-do", "monthly", "0.8"),
        ("/standards", "monthly", "0.8"),
        ("/faq", "monthly", "0.8"),
        ("/openings", "weekly", "0.8"),
        ("/apply", "weekly", "0.8"),
        ("/resources", "weekly", "0.7"),
        ("/veterans", "monthly", "0.7"),
        ("/referrals", "monthly", "0.7"),
        ("/families", "monthly", "0.7"),
        ("/contact", "weekly", "0.7"),
        ("/tour", "weekly", "0.7"),
        ("/policies", "monthly", "0.6"),
        ("/operator-resources", "monthly", "0.6"),
        ("/impact", "monthly", "0.6"),
        ("/stories", "weekly", "0.6"),
        ("/programs", "monthly", "0.5"),
        ("/careers", "monthly", "0.5"),
        ("/shop", "monthly", "0.5"),
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


@public_bp.get("/manifest.json")
def manifest():
    return send_from_directory(current_app.static_folder, "manifest.json")


# ── Homepage ─────────────────────────────────────────────────

@public_bp.get("/")
def index():
    layout = None
    blocks = None
    try:
        layout = PageLayout.query.filter_by(page="home").first()
    except Exception:
        pass
    if layout and layout.layout_json:
        try:
            data = json.loads(layout.layout_json)
            blocks = data.get("blocks") if isinstance(data, dict) else None
        except Exception:
            blocks = None
    try:
        openings_preview = Opening.query.filter_by(status="published").order_by(Opening.created_at.desc()).limit(3).all()
    except Exception:
        openings_preview = []
    return render_template("index.html", title="Overcomers — Transformative Thinking & Restorative Community", page_blocks=blocks, openings_preview=openings_preview)


# ── Core pages ───────────────────────────────────────────────

@public_bp.get("/what-we-do")
def what_we_do():
    return render_template("whatwedo.html", title="What We Do")


@public_bp.get("/guide")
def guide():
    return render_template("guide.html", title="Recovery Residence Guide — Start Here")


@public_bp.get("/faq")
def faq():
    return render_template("faq.html", title="Frequently Asked Questions")


@public_bp.get("/standards")
def standards():
    return render_template("standards.html", title="Our Standards — Safety & Integrity")


@public_bp.get("/resources")
def resources():
    return render_template("resources.html", title="Resources")


@public_bp.get("/operator-resources")
def operator_resources():
    return render_template("operator_resources.html", title="Operating Documents & Resources")


@public_bp.get("/impact")
def impact():
    return render_template("impact.html", title="Impact")


@public_bp.get("/veterans")
def veterans():
    return render_template("veterans.html", title="Veterans Support")


@public_bp.get("/referrals")
def referrals():
    return render_template("referrals.html", title="For Referral Partners")


@public_bp.get("/families")
def families():
    return render_template("families.html", title="For Families & Loved Ones")


@public_bp.get("/policies")
def policies():
    return render_template("policies.html", title="Policies & Documents")


@public_bp.get("/programs")
def programs():
    return render_template("programs.html", title="Programs & Workshops")


@public_bp.get("/classes")
def classes():
    return render_template("classes.html", title="Classes")


@public_bp.get("/kids-support")
def kids_support():
    return render_template("kids_support.html", title="Kids & Family Support")


@public_bp.get("/partnerships")
def partnerships():
    return render_template("partnerships.html", title="Jobs & Partnerships")


@public_bp.get("/careers")
def careers():
    return render_template("careers.html", title="Careers")


@public_bp.get("/privacy")
def privacy():
    return render_template("legal/privacy.html", title="Privacy Policy")


@public_bp.get("/terms")
def terms():
    return render_template("legal/terms.html", title="Terms of Use")


@public_bp.get("/shop")
def shop():
    return render_template("shop.html", title="Support the Mission")


@public_bp.get("/checkout")
def checkout():
    # No active checkout — redirect to shop
    return redirect(url_for("public.shop"), code=302)


# ── Contact ──────────────────────────────────────────────────

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

    flash("Thanks — we got your message and will respond within 24 hours.", "success")
    return redirect(url_for("public.contact"))


# ── Tour Request ─────────────────────────────────────────────

@public_bp.get("/tour")
def tour():
    form = TourRequestForm()
    return render_template("tour.html", form=form, title="Schedule a Tour")


@public_bp.post("/tour")
@limiter.limit("10 per hour")
def tour_post():
    form = TourRequestForm()
    if not form.validate_on_submit():
        flash("Please check the form and try again.", "error")
        return render_template("tour.html", form=form, title="Schedule a Tour"), 400

    req = TourRequest(
        name=form.name.data.strip(),
        email=form.email.data.strip().lower(),
        phone=(form.phone.data.strip() if form.phone.data else None),
        preferred_time=(form.preferred_time.data.strip() if form.preferred_time.data else None),
        notes=(form.notes.data.strip() if form.notes.data else None),
    )
    db.session.add(req)
    db.session.commit()

    body = (
        "New tour request\n\n"
        f"Name: {req.name}\n"
        f"Email: {req.email}\n"
        f"Phone: {req.phone or '-'}\n"
        f"Preferred time: {req.preferred_time or '-'}\n\n"
        f"Notes:\n{req.notes or '-'}\n"
    )
    send_email(to_email=current_app.config.get("NOTIFY_EMAIL"), subject="[Overcomers] Tour request", body=body)

    flash("Tour request sent! We'll respond within 24 hours to confirm a time.", "success")
    return redirect(url_for("public.tour"))


# ── Apply ────────────────────────────────────────────────────

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

    flash("Application received — we'll reach out within 24 hours.", "success")
    return redirect(url_for("public.apply"))


# ── Interest signup (no openings) ────────────────────────────

@public_bp.post("/interest")
@limiter.limit("10 per hour")
def interest_post():
    form = InterestForm()
    if form.validate_on_submit():
        signup = InterestSignup(email=form.email.data.strip().lower())
        try:
            db.session.add(signup)
            db.session.commit()
            flash("You're on the list! We'll email you when a spot opens.", "success")
        except Exception:
            db.session.rollback()
            flash("You're already on the list.", "info")
    else:
        flash("Please enter a valid email.", "error")
    return redirect(url_for("public.openings"))


# ── Openings ─────────────────────────────────────────────────

@public_bp.get("/openings")
def openings():
    interest_form = InterestForm()
    try:
        items = (
            Opening.query.filter_by(status="published")
            .order_by(Opening.created_at.desc())
            .limit(100)
            .all()
        )
    except Exception:
        items = []
    return render_template("openings.html", openings=items, interest_form=interest_form, title="Upcoming Openings")


@public_bp.get("/openings/<slug>")
def opening_detail(slug: str):
    row = Opening.query.filter_by(slug=slug, status="published").first_or_404()
    return render_template("opening_detail.html", opening=row, title=row.title)


# ── Stories ──────────────────────────────────────────────────

@public_bp.get("/stories")
def stories():
    try:
        items = Story.query.filter_by(status="approved").order_by(Story.created_at.desc()).limit(50).all()
    except Exception:
        items = []
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
                subject="New story submission (Overcomers)",
                body=f"Title: {story.title}\nAuthor: {story.author_name or '(not provided)'}\n\nReview in /admin/stories",
            )
        flash("Thanks! Your story was submitted for review.", "success")
        return redirect(url_for("public.stories"))
    return render_template("story_submit.html", form=form, title="Share a story")


# ── Legacy redirects (.html → clean URLs) ────────────────────

_LEGACY_REDIRECTS = {
    "/index.html": "public.index",
    "/shop.html": "public.shop",
    "/resources.html": "public.resources",
    "/contact.html": "public.contact",
    "/what-we-do.html": "public.what_we_do",
    "/careers.html": "public.careers",
    "/impact.html": "public.impact",
    "/guide.html": "public.guide",
    "/faq.html": "public.faq",
    "/standards.html": "public.standards",
    "/tour.html": "public.tour",
    "/veterans.html": "public.veterans",
    "/families.html": "public.families",
    "/referrals.html": "public.referrals",
    "/policies.html": "public.policies",
}

for _path, _endpoint in _LEGACY_REDIRECTS.items():
    def _make_redirect(ep):
        def _redir():
            return redirect(url_for(ep), code=301)
        return _redir
    _fn = _make_redirect(_endpoint)
    _fn.__name__ = f"legacy_{_endpoint.replace('.', '_')}"
    public_bp.add_url_rule(_path, _fn.__name__, _fn, methods=["GET"])


# Convenience: /login and /register without /auth prefix
@public_bp.get("/login")
def login_shortcut():
    return redirect(url_for("auth.login"), code=302)


@public_bp.get("/register")
def register_shortcut():
    return redirect(url_for("auth.register"), code=302)
