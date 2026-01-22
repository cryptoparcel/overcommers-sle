from flask import Blueprint, render_template, redirect, url_for, request, Response
from flask_login import login_required, current_user
from ..models import Application, SiteSettings
from .. import db
import csv
import io
import datetime

admin_bp = Blueprint("admin", __name__)

def require_admin():
    return current_user.is_authenticated and current_user.role == "admin"

@admin_bp.get("/")
@login_required
def dashboard():
    if not require_staff():
        return redirect(url_for("public.index"))
    total = Application.query.count()
    new = Application.query.filter_by(status="New").count()
    return render_template("admin_dashboard.html", title="Admin — OVERCOMERS | SLE", counts={"total": total, "new": new})

@admin_bp.get("/applications")
@login_required
def applications():
    if not require_staff():
        return redirect(url_for("public.index"))
    apps = Application.query.order_by(Application.created_at.desc()).all()
    return render_template("admin_applications.html", title="Applications — OVERCOMERS | SLE", applications=apps)

@admin_bp.post("/applications/<int:app_id>")
@login_required
def update_application(app_id: int):
    if not require_staff():
        return redirect(url_for("public.index"))
    status = request.form.get("status") or "New"
    a = Application.query.get_or_404(app_id)
    a.status = status
    db.session.commit()
    return redirect(url_for("admin.applications"))

@admin_bp.get("/applications/export.csv")
@login_required
def export_applications():
    if not require_admin():
        return redirect(url_for("public.index"))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "name", "email", "phone", "message", "status"])
    for a in Application.query.order_by(Application.created_at.desc()).all():
        writer.writerow([a.id, a.created_at.isoformat(), a.name, a.email, a.phone, (a.message or ""), a.status])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=applications.csv"})

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not require_admin():
        return redirect(url_for("public.index"))
    s = SiteSettings.query.first()
    if request.method == "POST":
        s.home_headline = request.form.get("home_headline") or s.home_headline
        s.home_subhead = request.form.get("home_subhead") or s.home_subhead
        s.home_lead = request.form.get("home_lead") or s.home_lead
        s.youtube_url = request.form.get("youtube_url") or ""
        s.hero_image_url = request.form.get("hero_image_url") or ""
        s.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        return redirect(url_for("admin.settings"))
    return render_template("admin_settings.html", title="Settings — OVERCOMERS | SLE", settings=s)



def require_staff():
    return current_user.is_authenticated and current_user.role in ("admin","staff")
