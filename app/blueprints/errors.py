from __future__ import annotations
from flask import Blueprint, render_template, current_app

errors_bp = Blueprint("errors", __name__)

@errors_bp.app_errorhandler(404)
def not_found(_e):
    return render_template("404.html", title="Not found"), 404

@errors_bp.app_errorhandler(403)
def forbidden(_e):
    return render_template("403.html", title="Forbidden"), 403

@errors_bp.app_errorhandler(500)
def server_error(e):
    current_app.logger.exception("500 error: %s", e)
    return render_template("500.html", title="Error"), 500
