from __future__ import annotations

from datetime import datetime
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Application, ContactMessage, Story, User, PageLayout
from ..utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return redirect(url_for("admin.applications"))


@admin_bp.route("/applications")
@login_required
@admin_required
def applications():
    items = Application.query.order_by(Application.created_at.desc()).limit(200).all()
    return render_template("admin/applications.html", applications=items)


@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(300).all()
    return render_template("admin/messages.html", messages=items)


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    items = User.query.order_by(User.created_at.desc()).limit(300).all()
    return render_template("admin/users.html", users=items)


@admin_bp.route("/stories")
@login_required
@admin_required
def stories():
    status = request.args.get("status", "pending")
    q = Story.query
    if status in {"pending", "approved", "rejected"}:
        q = q.filter_by(status=status)
    items = q.order_by(Story.created_at.desc()).limit(300).all()
    return render_template("admin/stories.html", stories=items, status=status)


@admin_bp.post("/stories/<int:story_id>/approve")
@login_required
@admin_required
def approve_story(story_id: int):
    story = Story.query.get_or_404(story_id)
    story.status = "approved"
    story.reviewed_at = datetime.utcnow()
    story.reviewed_by = current_user.id
    # prefer current_user if available
    db.session.commit()
    flash("Story approved.", "success")
    return redirect(url_for("admin.stories", status="pending"))


@admin_bp.post("/stories/<int:story_id>/reject")
@login_required
@admin_required
def reject_story(story_id: int):
    story = Story.query.get_or_404(story_id)
    story.status = "rejected"
    story.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash("Story rejected.", "info")
    return redirect(url_for("admin.stories", status="pending"))


@admin_bp.post("/stories/<int:story_id>/delete")
@login_required
@admin_required
def delete_story(story_id: int):
    story = Story.query.get_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    flash("Story deleted.", "info")
    return redirect(url_for("admin.stories", status="pending"))


def _default_home_layout_json() -> str:
    """Starter layout the user can move around in the Page Builder."""
    payload = {
        "version": 1,
        "canvas": {"minHeight": 520},
        "blocks": [
            {
                "id": "resources",
                "type": "card",
                "x": 0,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Resources",
                    "body": "Simple, kid-friendly and family-friendly links to get help, learn next steps, and find local support.",
                    "buttons": [{"label": "Go to resources", "href": "/resources"}],
                },
            },
            {
                "id": "shop",
                "type": "card",
                "x": 51,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Shop & support",
                    "body": "Placeholder shop page for sponsorship, donations, and community support items. We can add real checkout later.",
                    "buttons": [
                        {"label": "Visit shop", "href": "/shop"},
                        {"label": "Checkout", "href": "/checkout"},
                    ],
                    "note": "This is not legal advice or medical advice. Always call 911 in an emergency.",
                },
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


@admin_bp.route("/page-builder", methods=["GET", "POST"])
@admin_required
def page_builder():
    """Lightweight drag-and-drop page builder for the homepage."""

    layout = PageLayout.query.filter_by(page="home").first()
    if not layout:
        layout = PageLayout(page="home", layout_json=_default_home_layout_json())
        db.session.add(layout)
        db.session.commit()

    if request.method == "POST":
        action = request.form.get("action", "save")
        if action == "reset":
            layout.layout_json = _default_home_layout_json()
            db.session.commit()
            flash("Page layout reset to the default starter layout.", "info")
            return redirect(url_for("admin.page_builder"))

        raw = (request.form.get("layout_json") or "").strip()
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or "blocks" not in parsed or not isinstance(parsed["blocks"], list):
                raise ValueError("Invalid layout format")
        except Exception:
            flash("Could not save layout: invalid JSON.", "error")
            return redirect(url_for("admin.page_builder"))

        layout.layout_json = raw
        layout.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Page layout saved.", "success")
        return redirect(url_for("admin.page_builder"))

    # GET
    try:
        parsed = json.loads(layout.layout_json or "{}")
    except Exception:
        parsed = json.loads(_default_home_layout_json())

    raw = layout.layout_json or _default_home_layout_json()
    return render_template(
        "admin/page_builder.html",
        raw_json=raw,
        parsed=parsed,
        active="builder",
    )



