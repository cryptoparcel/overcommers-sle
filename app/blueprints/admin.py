from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from ..extensions import db
from ..models import Application, ContactMessage, Story, User
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
