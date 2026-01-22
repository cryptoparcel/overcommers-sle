import re

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user
from ..models import User
from .. import db
from .. import limiter

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        identifier = (request.form.get("identifier") or "").strip().lower()
        username = (request.form.get("username") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip() or None
        password = request.form.get("password") or ""
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        if not user or not user.check_password(password):
            return render_template("login.html", title="Login — OVERCOMERS | SLE", error="Invalid email or password.")
        login_user(user)
        return redirect(url_for("public.index"))
    return render_template("login.html", title="Login — OVERCOMERS | SLE")

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        identifier = (request.form.get("identifier") or "").strip().lower()
        username = (request.form.get("username") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip() or None
        password = request.form.get("password") or ""
        if len(password) < 8:
            return render_template("register.html", title="Create account — OVERCOMERS | SLE", error="Password must be at least 8 characters.")
        if User.query.filter_by(email=email).first():
            return render_template("register.html", title="Create account — OVERCOMERS | SLE", error="That email is already registered.")
        if User.query.filter_by(username=username).first():
            return render_template("register.html", title="Create account — OVERCOMERS | SLE", error="That username is already taken.")

        #
            return render_template("register.html", title="Create account — OVERCOMERS | SLE", error="An account with that email already exists.")
        u = User(email=email, role="resident")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        login_user(u)
        return redirect(url_for("public.index"))
    return render_template("register.html", title="Create account — OVERCOMERS | SLE")

@auth_bp.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.index"))
