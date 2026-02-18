
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for, Response, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import Application, ContactMessage, Story, User, PageLayout, Opening, TourRequest, InterestSignup, DepositPayment, ActivityLog
from ..utils import admin_required, log_activity
from ..seed import _default_home_layout_json  # uses same defaults
from ..forms import OpeningForm
from ..utils import slugify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    # real counts (no placeholders)
    new_count = Application.query.filter_by(status="new").count()
    total_count = Application.query.count()
    pending_stories = Story.query.filter_by(status="pending").count()
    msg_count = ContactMessage.query.count()
    try:
        tour_count = TourRequest.query.count()
    except Exception:
        tour_count = 0
    try:
        interest_count = InterestSignup.query.count()
    except Exception:
        interest_count = 0
    try:
        deposit_count = DepositPayment.query.filter_by(status="paid").count()
        deposit_pending = DepositPayment.query.filter_by(status="pending").count()
    except Exception:
        deposit_count = 0
        deposit_pending = 0

    # Activity stats
    try:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        total_logs = ActivityLog.query.count()
        today_views = ActivityLog.query.filter(
            ActivityLog.created_at >= today_start,
            ActivityLog.category == "page_view"
        ).count()
        today_submissions = ActivityLog.query.filter(
            ActivityLog.created_at >= today_start,
            ActivityLog.category == "form_submit"
        ).count()
        week_views = ActivityLog.query.filter(
            ActivityLog.created_at >= week_start,
            ActivityLog.category == "page_view"
        ).count()
        failed_logins = ActivityLog.query.filter(
            ActivityLog.action == "login_failed",
            ActivityLog.created_at >= week_start
        ).count()
        recent_activity = ActivityLog.query.filter(
            ActivityLog.category.in_(["form_submit", "payment", "auth", "admin_action"])
        ).order_by(ActivityLog.created_at.desc()).limit(8).all()
    except Exception:
        total_logs = today_views = today_submissions = week_views = failed_logins = 0
        recent_activity = []

    return render_template(
        "admin/dashboard.html",
        title="Admin dashboard",
        counts={
            "new": new_count,
            "total": total_count,
            "pending_stories": pending_stories,
            "messages": msg_count,
            "tours": tour_count,
            "interest": interest_count,
            "deposits_paid": deposit_count,
            "deposits_pending": deposit_pending,
        },
        activity={
            "total_logs": total_logs,
            "today_views": today_views,
            "today_submissions": today_submissions,
            "week_views": week_views,
            "failed_logins": failed_logins,
        },
        recent_activity=recent_activity,
        active="dashboard",
    )

@admin_bp.route("/applications")
@login_required
@admin_required
def applications():
    items = Application.query.order_by(Application.created_at.desc()).limit(200).all()
    return render_template("admin/applications.html", applications=items, active="applications", title="Applications")

@admin_bp.post("/applications/<int:app_id>/status")
@login_required
@admin_required
def update_application(app_id: int):
    row = Application.query.get_or_404(app_id)
    status = (request.form.get("status") or "").strip().lower()
    if status not in {"new", "reviewed", "approved", "rejected"}:
        flash("Invalid status.", "error")
        return redirect(url_for("admin.applications"))
    row.status = status
    db.session.commit()

    # Activity log
    try:
        from ..utils import log_activity
        log_activity(action=f"application_status_changed:{status}", category="admin_action",
                     details=f"Application #{row.id} ({row.full_name}) -> {status}",
                     resource_type="application", resource_id=row.id)
    except Exception:
        pass

    flash("Application status updated.", "success")
    return redirect(url_for("admin.applications"))

@admin_bp.get("/applications/export.csv")
@login_required
@admin_required
def export_applications():
    items = Application.query.order_by(Application.created_at.desc()).limit(5000).all()

    def esc(v: str) -> str:
        v = (v or "")
        # Prevent CSV formula injection (=, +, -, @, tab, CR)
        if v and v[0] in ("=", "+", "-", "@", "\t", "\r"):
            v = "'" + v
        v = v.replace('"', '""')
        return f'"{v}"'

    lines = ["created_at,full_name,email,phone,status,message"]
    for a in items:
        lines.append(",".join([
            esc(a.created_at.isoformat() if a.created_at else ""),
            esc(a.full_name),
            esc(a.email),
            esc(a.phone or ""),
            esc(a.status or ""),
            esc(a.message or ""),
        ]))

    return Response(
        "\n".join(lines),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=applications.csv"},
    )

@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(300).all()
    return render_template("admin/messages.html", messages=items, active="messages", title="Messages")

@admin_bp.route("/users")
@login_required
@admin_required
def users():
    items = User.query.order_by(User.created_at.desc()).limit(300).all()
    return render_template("admin/users.html", users=items, active="users", title="Users")

@admin_bp.route("/stories")
@login_required
@admin_required
def stories():
    status = request.args.get("status", "pending")
    q = Story.query
    if status in {"pending", "approved", "rejected"}:
        q = q.filter_by(status=status)
    items = q.order_by(Story.created_at.desc()).limit(300).all()
    return render_template("admin/stories.html", stories=items, status=status, active="stories", title="Stories")

@admin_bp.post("/stories/<int:story_id>/approve")
@login_required
@admin_required
def approve_story(story_id: int):
    story = Story.query.get_or_404(story_id)
    story.status = "approved"
    story.reviewed_at = datetime.now(timezone.utc)
    story.reviewed_by = current_user.id
    db.session.commit()
    flash("Story approved.", "success")
    return redirect(url_for("admin.stories", status="pending"))

@admin_bp.post("/stories/<int:story_id>/reject")
@login_required
@admin_required
def reject_story(story_id: int):
    story = Story.query.get_or_404(story_id)
    story.status = "rejected"
    story.reviewed_at = datetime.now(timezone.utc)
    story.reviewed_by = current_user.id
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

@admin_bp.route("/page-builder", methods=["GET", "POST"])
@login_required
@admin_required
def page_builder():
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
        layout.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Page layout saved.", "success")
        return redirect(url_for("admin.page_builder"))

    try:
        parsed = json.loads(layout.layout_json or "{}")
    except Exception:
        parsed = json.loads(_default_home_layout_json())

    raw = layout.layout_json or _default_home_layout_json()
    return render_template("admin/page_builder.html", raw_json=raw, layout_data=parsed, active="builder", title="Page Builder")


# ----------------------------
# Openings (Admin)
# ----------------------------

def _photos_to_json(textarea_val: str) -> str | None:
    """Convert newline-separated URLs to JSON array string."""
    if not textarea_val:
        return None
    urls = [u.strip() for u in textarea_val.strip().splitlines() if u.strip()]
    return json.dumps(urls) if urls else None


def _photos_to_textarea(json_val: str | None) -> str:
    """Convert JSON array string back to newline-separated URLs for the form."""
    if not json_val:
        return ""
    try:
        return "\n".join(json.loads(json_val))
    except Exception:
        return ""


@admin_bp.get("/openings")
@login_required
@admin_required
def openings():
    items = Opening.query.order_by(Opening.created_at.desc()).limit(300).all()
    return render_template("admin/openings_list.html", openings=items, active="openings", title="Openings")


@admin_bp.route("/openings/new", methods=["GET", "POST"])
@login_required
@admin_required
def openings_new():
    form = OpeningForm()
    if request.method == "GET":
        # sensible defaults for your area
        form.state.data = form.state.data or "CA"
        form.city.data = form.city.data or "Grover Beach"
        form.hide_price.data = True
        form.status.data = "draft"
        return render_template("admin/opening_form.html", form=form, active="openings", title="New opening")

    if not form.validate_on_submit():
        flash("Please fix the form errors and try again.", "error")
        return render_template("admin/opening_form.html", form=form, active="openings", title="New opening"), 400

    # ensure slug uniqueness
    slug = slugify(form.slug.data)
    base = slug
    i = 2
    while Opening.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{i}"
        i += 1

    row = Opening(
        title=form.title.data.strip(),
        slug=slug,
        city=(form.city.data or "").strip() or None,
        state=(form.state.data or "").strip() or None,
        beds_available=form.beds_available.data or 1,
        available_on=form.available_on.data,
        price_monthly=(form.price_monthly.data or "").strip() or None,
        deposit=(form.deposit.data or "").strip() or None,
        hide_price=bool(form.hide_price.data),
        summary=(form.summary.data or "").strip() or None,
        details=(form.details.data or "").strip() or None,
        included=(form.included.data or "").strip() or None,
        house_rules=(form.house_rules.data or "").strip() or None,
        contact_name=(form.contact_name.data or "").strip() or None,
        contact_email=(form.contact_email.data or "").strip().lower() or None,
        contact_phone=(form.contact_phone.data or "").strip() or None,
        photos_json=_photos_to_json(form.photos.data),
        status=form.status.data,
    )
    db.session.add(row)
    db.session.commit()
    flash("Opening created.", "success")
    return redirect(url_for("admin.openings"))


@admin_bp.route("/openings/<int:opening_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def openings_edit(opening_id: int):
    row = Opening.query.get_or_404(opening_id)
    form = OpeningForm(obj=row)

    if request.method == "GET":
        form.photos.data = _photos_to_textarea(row.photos_json)
        return render_template("admin/opening_form.html", form=form, opening=row, active="openings", title="Edit opening")

    if not form.validate_on_submit():
        flash("Please fix the form errors and try again.", "error")
        return render_template("admin/opening_form.html", form=form, opening=row, active="openings", title="Edit opening"), 400

    # slug uniqueness (allow unchanged)
    new_slug = slugify(form.slug.data)
    if new_slug != row.slug:
        base = new_slug
        i = 2
        while Opening.query.filter(Opening.slug == new_slug, Opening.id != row.id).first() is not None:
            new_slug = f"{base}-{i}"
            i += 1
        row.slug = new_slug

    row.title = form.title.data.strip()
    row.city = (form.city.data or "").strip() or None
    row.state = (form.state.data or "").strip() or None
    row.beds_available = form.beds_available.data or 1
    row.available_on = form.available_on.data
    row.price_monthly = (form.price_monthly.data or "").strip() or None
    row.deposit = (form.deposit.data or "").strip() or None
    row.hide_price = bool(form.hide_price.data)
    row.summary = (form.summary.data or "").strip() or None
    row.details = (form.details.data or "").strip() or None
    row.included = (form.included.data or "").strip() or None
    row.house_rules = (form.house_rules.data or "").strip() or None
    row.contact_name = (form.contact_name.data or "").strip() or None
    row.contact_email = (form.contact_email.data or "").strip().lower() or None
    row.contact_phone = (form.contact_phone.data or "").strip() or None
    row.photos_json = _photos_to_json(form.photos.data)
    row.status = form.status.data

    db.session.commit()
    flash("Opening updated.", "success")
    return redirect(url_for("admin.openings"))


@admin_bp.post("/openings/<int:opening_id>/delete")
@login_required
@admin_required
def openings_delete(opening_id: int):
    row = Opening.query.get_or_404(opening_id)
    db.session.delete(row)
    db.session.commit()
    flash("Opening deleted.", "info")
    return redirect(url_for("admin.openings"))


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@admin_bp.post("/upload-photo")
@login_required
@admin_required
def upload_photo():
    """Handle photo file upload — saves to static/uploads/ and returns URL."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "No file selected"}), 400

    if not _allowed_file(f.filename):
        return jsonify({"error": "Only images allowed (jpg, png, gif, webp)"}), 400

    # Generate unique filename
    ext = f.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    safe_name = secure_filename(unique_name)

    upload_dir = current_app.config.get("UPLOAD_FOLDER", "app/static/uploads")
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, safe_name)
    f.save(filepath)

    # Return the static URL
    photo_url = url_for("static", filename=f"uploads/{safe_name}", _external=True)
    return jsonify({"url": photo_url, "filename": safe_name})


# ── Tour Requests (Admin) ────────────────────────────────────

@admin_bp.get("/tour-requests")
@login_required
@admin_required
def tour_requests():
    try:
        items = TourRequest.query.order_by(TourRequest.created_at.desc()).limit(300).all()
    except Exception:
        items = []
    return render_template("admin/tour_requests.html", tours=items, active="tours", title="Tour Requests")


# ── Interest List (Admin) ────────────────────────────────────

@admin_bp.get("/interest-list")
@login_required
@admin_required
def interest_list():
    try:
        items = InterestSignup.query.order_by(InterestSignup.created_at.desc()).limit(300).all()
    except Exception:
        items = []
    return render_template("admin/interest_list.html", signups=items, active="interest", title="Interest List")


# ── Deposit Payments (Admin) ─────────────────────────────────

@admin_bp.get("/deposits")
@login_required
@admin_required
def deposits():
    try:
        items = DepositPayment.query.order_by(DepositPayment.created_at.desc()).limit(300).all()
    except Exception:
        items = []
    return render_template("admin/deposits.html", deposits=items, active="deposits", title="Deposit Payments")


# ── Activity Logs (Admin) ────────────────────────────────────

@admin_bp.get("/activity-log")
@login_required
@admin_required
def activity_log():
    """View activity logs with filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = 50
    category = request.args.get("category", "")
    level = request.args.get("level", "")
    search = request.args.get("q", "").strip()

    q = ActivityLog.query

    if category:
        q = q.filter_by(category=category)
    if level:
        q = q.filter_by(level=level)
    if search:
        q = q.filter(
            db.or_(
                ActivityLog.action.ilike(f"%{search}%"),
                ActivityLog.details.ilike(f"%{search}%"),
                ActivityLog.ip_address.ilike(f"%{search}%"),
                ActivityLog.path.ilike(f"%{search}%"),
            )
        )

    pagination = q.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = pagination.items

    # Get distinct categories for filter dropdown
    try:
        categories = [r[0] for r in db.session.query(ActivityLog.category).distinct().all() if r[0]]
    except Exception:
        categories = []

    # Log counts for quick stats
    try:
        total_logs = ActivityLog.query.count()
        today_logs = ActivityLog.query.filter(
            ActivityLog.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).count()
        warning_count = ActivityLog.query.filter_by(level="warning").count()
        error_count = ActivityLog.query.filter_by(level="error").count()
    except Exception:
        total_logs = today_logs = warning_count = error_count = 0

    return render_template(
        "admin/activity_log.html",
        logs=items,
        pagination=pagination,
        categories=categories,
        current_category=category,
        current_level=level,
        current_search=search,
        total_logs=total_logs,
        today_logs=today_logs,
        warning_count=warning_count,
        error_count=error_count,
        active="activity",
        title="Activity Log",
    )


@admin_bp.get("/activity-log/export.csv")
@login_required
@admin_required
def export_activity_log():
    """Export activity logs as CSV."""
    items = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(10000).all()

    def esc(v: str) -> str:
        v = (v or "")
        if v and v[0] in ("=", "+", "-", "@", "\t", "\r"):
            v = "'" + v
        v = v.replace('"', '""')
        return f'"{v}"'

    lines = ["timestamp,action,category,level,user_id,ip_address,path,method,details,user_agent"]
    for log in items:
        lines.append(",".join([
            esc(log.created_at.isoformat() if log.created_at else ""),
            esc(log.action or ""),
            esc(log.category or ""),
            esc(log.level or ""),
            esc(str(log.user_id) if log.user_id else ""),
            esc(log.ip_address or ""),
            esc(log.path or ""),
            esc(log.method or ""),
            esc(log.details or ""),
            esc(log.user_agent or ""),
        ]))

    log_activity(action="activity_log_exported", category="admin_action",
                 details=f"Exported {len(items)} log entries")

    return Response(
        "\n".join(lines),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=activity_log_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"},
    )
