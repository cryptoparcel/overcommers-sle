from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, URL


username_re = Regexp(
    r"^[a-zA-Z0-9_]{3,32}$",
    message="Username must be 3–32 characters: letters, numbers, underscore.",
)


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    username = StringField("Username", validators=[DataRequired(), username_re])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])


class LoginForm(FlaskForm):
    username_or_email = StringField("Username or Email", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=1, max=128)])


class ApplyForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField("Phone (optional)", validators=[Optional(), Length(max=40)])
    message = TextAreaField("Anything you'd like us to know (optional)", validators=[Optional(), Length(max=2000)])


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=4000)])


class StorySubmitForm(FlaskForm):
    title = StringField("Story title", validators=[DataRequired(), Length(min=5, max=180)])
    author_name = StringField("Your name (optional)", validators=[Optional(), Length(max=120)])
    summary = StringField("Short summary (optional)", validators=[Optional(), Length(max=320)])
    image_url = StringField("Photo URL (optional)", validators=[Optional(), Length(max=500), URL()])
    body = TextAreaField("Your story", validators=[DataRequired(), Length(min=50, max=8000)])
    submit = SubmitField("Submit story for review")