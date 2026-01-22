from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, url_for, send_from_directory, current_app
from flask_login import login_required, current_user

from ..extensions import db, limiter
from ..forms import ApplyForm, ContactForm
from ..models import Application, ContactMessage
from ..utils.mailer import send_email

public_bp = Blueprint("public", __name__)


@public_bp.get("/favicon.ico")
def favicon():
    return send_from_directory(current_app.static_folder, "favicon.ico")


@public_bp.get("/")
def index():
    return render_template("index.html", title="Overcomers | SLE")


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

    # Optional email notification
    body = (
        "New contact message\n\n"
        f"Name: {msg.name}\n"
        f"Email: {msg.email}\n"
        f"Subject: {msg.subject}\n\n"
        f"{msg.message}\n"
    )
    send_email(subject=f"[Overcomers] Contact: {msg.subject}", body=body, to_email=current_app.config.get("NOTIFY_EMAIL"))

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
    send_email(subject="[Overcomers] New application", body=body, to_email=current_app.config.get("NOTIFY_EMAIL"))

    flash("Thanks — we’ll reach out soon.", "success")
    return redirect(url_for("public.apply"))


@public_bp.get("/privacy")
def privacy():
    return render_template("legal/privacy.html", title="Privacy Policy")


@public_bp.get("/terms")
def terms():
    return render_template("legal/terms.html", title="Terms of Use")


@public_bp.get("/admin/applications")
@login_required
def admin_applications():
    if not getattr(current_user, "is_admin", False):
        flash("Admins only.", "error")
        return redirect(url_for("public.index"))

    rows = Application.query.order_by(Application.created_at.desc()).limit(200).all()
    return render_template("admin/applications.html", rows=rows, title="Applications")
