
from __future__ import annotations

import secrets
from datetime import datetime, timezone, timedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db, limiter
from ..forms import SignupForm, LoginForm, ProfileForm, PasswordChangeForm, PasswordResetRequestForm, PasswordResetForm
from ..models import User, Event, EventRSVP
from ..utils.mailer import send_email

RESET_TOKEN_TTL_HOURS = 1

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


# ── Password reset ────────────────────────────────────────────

def _send_reset_email(user: User) -> None:
    reset_url = url_for("auth.reset_password", token=user.reset_token, _external=True)
    body = (
        f"Hi {user.name or user.username},\n\n"
        f"Someone asked to reset the password on your Overcomers account.\n\n"
        f"If it was you, click this link within the next {RESET_TOKEN_TTL_HOURS} hour(s) to pick a new password:\n"
        f"{reset_url}\n\n"
        f"If you didn't request this, you can safely ignore this email — your password won't change.\n\n"
        f"— The Overcomers Team\n"
        f"Grover Beach, CA\n"
    )
    send_email(
        to_email=user.email,
        subject="Reset your password — Overcomers",
        body=body,
    )


@auth_bp.get("/forgot-password")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("auth.account"))
    form = PasswordResetRequestForm()
    return render_template("auth/forgot_password.html", form=form, title="Reset password")


@auth_bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password_post():
    if current_user.is_authenticated:
        return redirect(url_for("auth.account"))
    form = PasswordResetRequestForm()
    if not form.validate_on_submit():
        flash("Please enter a valid email.", "error")
        return render_template("auth/forgot_password.html", form=form, title="Reset password"), 400

    email = form.email.data.strip().lower()
    user = User.query.filter_by(email=email).first()

    if user:
        user.reset_token = _generate_token()
        user.reset_token_expires = (
            datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=RESET_TOKEN_TTL_HOURS)
        )
        db.session.commit()
        try:
            _send_reset_email(user)
        except Exception:
            pass  # Don't leak mailer failures through the UI
        try:
            from ..utils import log_activity
            log_activity(action="password_reset_requested", category="auth",
                         details=f"user_id={user.id}", user_id=user.id, level="info")
        except Exception:
            pass

    # Same response whether or not the email exists — prevents enumeration
    flash("If an account with that email exists, we've sent a reset link. Check your inbox.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.get("/reset-password/<token>")
def reset_password(token: str):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        flash("That reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))
    form = PasswordResetForm()
    return render_template("auth/reset_password.html", form=form, token=token, title="Choose a new password")


@auth_bp.post("/reset-password/<token>")
@limiter.limit("10 per hour")
def reset_password_post(token: str):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc).replace(tzinfo=None):
        flash("That reset link is invalid or has expired. Request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = PasswordResetForm()
    if not form.validate_on_submit():
        flash("Please fix the form errors and try again.", "error")
        return render_template("auth/reset_password.html", form=form, token=token, title="Choose a new password"), 400

    user.set_password(form.new_password.data)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()

    try:
        from ..utils import log_activity
        log_activity(action="password_reset_completed", category="auth",
                     details=f"user_id={user.id}", user_id=user.id, level="warning")
    except Exception:
        pass

    flash("Your password has been updated. Log in with your new password.", "success")
    return redirect(url_for("auth.login"))


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

    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=3)
    try:
        joined_events = (
            Event.query
            .join(EventRSVP, EventRSVP.event_id == Event.id)
            .filter(EventRSVP.user_id == current_user.id)
            .filter(Event.status == "published")
            .filter(Event.start_date >= cutoff)
            .order_by(Event.start_date.asc())
            .limit(50)
            .all()
        )
    except Exception:
        joined_events = []

    return render_template(
        "auth/account.html",
        profile_form=profile_form,
        password_form=password_form,
        joined_events=joined_events,
        title="Account settings",
    )
