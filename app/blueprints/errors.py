from __future__ import annotations

from flask import Blueprint, render_template

errors_bp = Blueprint("errors", __name__)


@errors_bp.app_errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@errors_bp.app_errorhandler(500)
def server_error(_e):
    return render_template("500.html"), 500
