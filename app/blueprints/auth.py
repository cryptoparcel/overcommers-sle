from __future__ import annotations

from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db, limiter
from ..forms import SignupForm, LoginForm, ProfileForm, PasswordChangeForm
from ..models import User

auth_bp = Blueprint("auth", __name__)


# ── Convenience redirects (old bookmarks / typed URLs) ───────
@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = LoginForm()
    return render_template("auth/login.html", form=form, title="Login")


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login_post():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = LoginForm()
    if not form.validate_on_submit():
        flash("Please check the form and try again.", "error")
        return render_template("auth/login.html", form=form, title="Login"), 400

    ident = form.identifier.data.strip().lower()
    user = User.query.filter_by(email=ident).first() or User.query.filter_by(username=ident).first()
    if not user or not user.check_password(form.password.data):
        flash("Invalid email/username or password.", "error")
        return render_template("auth/login.html", form=form, title="Login"), 401

    # Track last login
    try:
        user.last_login = datetime.utcnow()
        db.session.commit()
    except Exception:
        pass

    login_user(user, remember=True)
    flash("Welcome back.", "success")

    # Redirect to next page if specified, otherwise home
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/"):
        return redirect(next_page)
    return redirect(url_for("public.index"))


@auth_bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = SignupForm()
    return render_template("auth/register.html", form=form, title="Create account")


@auth_bp.post("/register")
@limiter.limit("6 per hour")
def register_post():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))

    form = SignupForm()
    if not form.validate_on_submit():
        flash("Please check the form and try again.", "error")
        return render_template("auth/register.html", form=form, title="Create account"), 400

    email = form.email.data.strip().lower()
    username = form.username.data.strip()
    if User.query.filter_by(email=email).first():
        flash("Email already in use.", "error")
        return render_template("auth/register.html", form=form, title="Create account"), 409
    if User.query.filter_by(username=username).first():
        flash("Username already in use.", "error")
        return render_template("auth/register.html", form=form, title="Create account"), 409

    user = User(
        name=form.name.data.strip(),
        email=email,
        username=username,
        phone=(form.phone.data.strip() if form.phone.data else None),
    )
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    flash("Account created.", "success")
    return redirect(url_for("public.index"))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("public.index"))


@auth_bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    profile_form = ProfileForm(prefix="profile")
    password_form = PasswordChangeForm(prefix="password")

    if request.method == "GET":
        profile_form.name.data = current_user.name or ""
        profile_form.phone.data = getattr(current_user, "phone", "") or ""

    if profile_form.submit_profile.data and profile_form.validate_on_submit():
        current_user.name = profile_form.name.data.strip()
        current_user.phone = (profile_form.phone.data or "").strip() or None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.account"))

    if password_form.submit_password.data and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Current password is incorrect.", "error")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Password updated.", "success")
            return redirect(url_for("auth.account"))

    return render_template(
        "auth/account.html",
        profile_form=profile_form,
        password_form=password_form,
        title="Account settings",
    )
