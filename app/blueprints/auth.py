
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db, limiter
from ..forms import SignupForm, LoginForm, ProfileForm, PasswordChangeForm
from ..models import User
from ..utils.mailer import send_email

auth_bp = Blueprint("auth", __name__)


def _generate_token() -> str:
    """Generate a URL-safe 32-char confirmation token."""
    return secrets.token_urlsafe(24)


def _send_confirmation_email(user: User) -> None:
    """Send (or re-send) the email confirmation link."""
    if not user.confirm_token:
        user.confirm_token = _generate_token()
        db.session.commit()

    confirm_url = url_for("auth.confirm_email", token=user.confirm_token, _external=True)

    body = (
        f"Hi {user.name},\n\n"
        f"Thanks for creating an account with Overcomers.\n\n"
        f"Please confirm your email by clicking this link:\n"
        f"{confirm_url}\n\n"
        f"This link doesn't expire, so no rush.\n\n"
        f"If you didn't create this account, you can ignore this email.\n\n"
        f"— The Overcomers Team\n"
        f"Grover Beach, CA\n"
    )
    send_email(
        to_email=user.email,
        subject="Confirm your email — Overcomers",
        body=body,
    )


# ── Login ─────────────────────────────────────────────────────

@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("public.index"))
    form = LoginForm()
    return render_template("auth/login.html", form=form, title="Login")


@auth_bp.post("/login")
@limiter.limit("5 per minute")
@limiter.limit("20 per hour")
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
        # Log failed login attempt
        try:
            from ..utils import log_activity
            log_activity(action="login_failed", category="auth", details=f"Attempted: {ident}", level="warning")
        except Exception:
            pass
        flash("Invalid email/username or password.", "error")
        return render_template("auth/login.html", form=form, title="Login"), 401

    # Track last login
    try:
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
    except Exception:
        pass

    login_user(user, remember=True)

    # Log successful login
    try:
        from ..utils import log_activity
        log_activity(action="login_success", category="auth", details=f"User: {user.email}", user_id=user.id)
    except Exception:
        pass

    if not user.email_confirmed:
        flash("Welcome back — please check your inbox and confirm your email when you get a chance.", "info")
    else:
        flash("Welcome back.", "success")

    # Redirect to next page if specified, otherwise home
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/") and not next_page.startswith("//"):
        return redirect(next_page)
    return redirect(url_for("public.index"))


# ── Register ──────────────────────────────────────────────────

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
        flash("An account with this email or username already exists.", "error")
        return render_template("auth/register.html", form=form, title="Create account"), 409
    if User.query.filter_by(username=username).first():
        flash("An account with this email or username already exists.", "error")
        return render_template("auth/register.html", form=form, title="Create account"), 409

    user = User(
        name=form.name.data.strip(),
        email=email,
        username=username,
        phone=(form.phone.data.strip() if form.phone.data else None),
        email_confirmed=False,
        confirm_token=_generate_token(),
    )
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()

    # Send confirmation email
    try:
        _send_confirmation_email(user)
    except Exception:
        pass  # Don't block registration if email fails

    login_user(user, remember=True)
    flash("Account created — we sent a confirmation link to your email.", "success")

    # Log registration
    try:
        from ..utils import log_activity
        log_activity(action="register", category="auth", details=f"New user: {email}", user_id=user.id, resource_type="user", resource_id=user.id)
    except Exception:
        pass

    return redirect(url_for("public.index"))


# ── Email confirmation ────────────────────────────────────────

@auth_bp.get("/confirm/<token>")
def confirm_email(token: str):
    """User clicks the link in their confirmation email."""
    user = User.query.filter_by(confirm_token=token).first()

    if not user:
        flash("Invalid or expired confirmation link.", "error")
        return redirect(url_for("public.index"))

    if user.email_confirmed:
        flash("Your email is already confirmed.", "info")
        return redirect(url_for("public.index"))

    user.email_confirmed = True
    user.confirm_token = None  # Single-use token
    db.session.commit()

    # Log them in if not already
    if not current_user.is_authenticated:
        login_user(user, remember=True)

    flash("Email confirmed — you're all set!", "success")
    return redirect(url_for("public.index"))


@auth_bp.post("/resend-confirmation")
@login_required
@limiter.limit("3 per hour")
def resend_confirmation():
    """Re-send the confirmation email."""
    if current_user.email_confirmed:
        flash("Your email is already confirmed.", "info")
        return redirect(url_for("auth.account"))

    try:
        _send_confirmation_email(current_user)
        flash("Confirmation email sent — check your inbox.", "success")
    except Exception:
        flash("Couldn't send email right now. Try again later.", "error")

    return redirect(url_for("auth.account"))


# ── Logout ────────────────────────────────────────────────────

@auth_bp.post("/logout")
@login_required
def logout():
    uid = current_user.id
    logout_user()
    try:
        from ..utils import log_activity
        log_activity(action="logout", category="auth", user_id=uid)
    except Exception:
        pass
    flash("Logged out.", "success")
    return redirect(url_for("public.index"))


# ── Account settings ──────────────────────────────────────────

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
