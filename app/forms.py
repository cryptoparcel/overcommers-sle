
from __future__ import annotations

from flask import current_app
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, HiddenField, IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, URL, EqualTo, ValidationError
import requests

username_re = Regexp(
    r"^[a-zA-Z0-9_]{3,32}$",
    message="Username must be 3–32 characters: letters, numbers, underscore.",
)

def _recaptcha_enabled() -> bool:
    cfg = current_app.config
    return bool(cfg.get("RECAPTCHA_SITE_KEY")) and bool(cfg.get("RECAPTCHA_SECRET_KEY"))

def validate_recaptcha(response_token: str) -> bool:
    cfg = current_app.config
    if not _recaptcha_enabled():
        return True
    if not response_token:
        return False
    try:
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": cfg["RECAPTCHA_SECRET_KEY"], "response": response_token},
            timeout=8,
        )
        data = r.json()
        return bool(data.get("success"))
    except Exception:
        return False


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    username = StringField("Username", validators=[DataRequired(), username_re])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    identifier = StringField("Email or username", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ApplyForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    message = TextAreaField("Anything we should know? (optional)", validators=[Optional(), Length(max=2000)])
    recaptcha_token = HiddenField("recaptcha_token")
    submit = SubmitField("Submit application")

    def validate_recaptcha_token(self, field):
        if _recaptcha_enabled() and not validate_recaptcha(field.data):
            raise ValidationError("Please complete the reCAPTCHA and try again.")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=4000)])
    recaptcha_token = HiddenField("recaptcha_token")
    submit = SubmitField("Send")

    def validate_recaptcha_token(self, field):
        if _recaptcha_enabled() and not validate_recaptcha(field.data):
            raise ValidationError("Please complete the reCAPTCHA and try again.")


class TourRequestForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    preferred_time = StringField("Preferred day/time (optional)", validators=[Optional(), Length(max=200)])
    notes = TextAreaField("Anything else? (optional)", validators=[Optional(), Length(max=2000)])
    recaptcha_token = HiddenField("recaptcha_token")
    submit = SubmitField("Request tour")

    def validate_recaptcha_token(self, field):
        if _recaptcha_enabled() and not validate_recaptcha(field.data):
            raise ValidationError("Please complete the reCAPTCHA and try again.")


class InterestForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    submit = SubmitField("Notify me")


class StorySubmitForm(FlaskForm):
    title = StringField("Story title", validators=[DataRequired(), Length(min=5, max=180)])
    author_name = StringField("Your name (optional)", validators=[Optional(), Length(max=120)])
    summary = StringField("Short summary (optional)", validators=[Optional(), Length(max=320)])
    image_url = StringField("Photo URL (optional)", validators=[Optional(), Length(max=500), URL()])
    body = TextAreaField("Your story", validators=[DataRequired(), Length(min=50, max=8000)])
    recaptcha_token = HiddenField("recaptcha_token")
    submit = SubmitField("Submit story for review")

    def validate_recaptcha_token(self, field):
        if _recaptcha_enabled() and not validate_recaptcha(field.data):
            raise ValidationError("Please complete the reCAPTCHA and try again.")


class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    submit_profile = SubmitField("Save changes")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_new_password = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit_password = SubmitField("Update password")


class OpeningForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=180)])
    slug = StringField("Slug (URL)", validators=[DataRequired(), Length(max=220)])

    city = StringField("City", validators=[Optional(), Length(max=120)])
    state = StringField("State", validators=[Optional(), Length(max=64)], default="CA")

    beds_available = IntegerField("Beds available", validators=[DataRequired()], default=1)
    available_on = DateField("Available on (optional)", validators=[Optional()], format="%Y-%m-%d")

    price_monthly = StringField("Monthly price (optional)", validators=[Optional(), Length(max=60)], default="$1,000 / month")
    deposit = StringField("Deposit (optional)", validators=[Optional(), Length(max=60)], default="$1,000 deposit")
    hide_price = BooleanField("Hide pricing publicly (recommended)", default=True)

    summary = TextAreaField("Short summary", validators=[Optional(), Length(max=320)])
    details = TextAreaField("Details", validators=[Optional()])
    included = TextAreaField("What's included (amenities)", validators=[Optional()])
    house_rules = TextAreaField("House rules / expectations", validators=[Optional()])

    contact_name = StringField("Contact name", validators=[Optional(), Length(max=120)])
    contact_email = StringField("Contact email", validators=[Optional(), Email(), Length(max=255)])
    contact_phone = StringField("Contact phone", validators=[Optional(), Length(max=60)])

    status = SelectField(
        "Status",
        choices=[("draft", "Draft"), ("published", "Published"), ("archived", "Archived")],
        validators=[DataRequired()],
        default="draft",
    )

    submit = SubmitField("Save opening")
