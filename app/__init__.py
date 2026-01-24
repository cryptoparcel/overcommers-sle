from __future__ import annotations

import json
import os

from flask import Flask

from .extensions import db, login_manager, limiter, csrf
from . import login  # noqa: F401
from .config import Config
from .blueprints.public import public_bp
from .blueprints.auth import auth_bp
from .blueprints.errors import errors_bp
from .blueprints.admin import admin_bp
from .models import PageLayout


def create_app() -> Flask:
    """Application factory for Overcomers SLE."""
    app = Flask(__name__, instance_relative_config=False)

    # Load configuration
    app.config.from_object(Config())

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(errors_bp)
    app.register_blueprint(admin_bp)

    # Create tables (simple bootstrap; for production prefer migrations)
    with app.app_context():
        db.create_all()
        _ensure_default_page_layouts()

    return app


def _ensure_default_page_layouts() -> None:
    """Create default PageLayout records if they don't exist.

    This enables the 'Option C' admin Page Builder out of the box.
    """

    if PageLayout.query.filter_by(page="home").first():
        return

    default = {
        "version": 1,
        "canvas": {"minHeight": 520},
        "blocks": [
            {
                "id": "resources",
                "type": "card",
                "x": 0,
                "y": 0,
                "w": 48,
                "h": 220,
                "content": {
                    "title": "Resources",
                    "body": "Simple, kid-friendly and family-friendly links to get help, learn next steps, and find local support.",
                    "button_label": "Go to resources",
                    "button_url": "/resources",
                },
            },
            {
                "id": "shop",
                "type": "card",
                "x": 52,
                "y": 0,
                "w": 48,
                "h": 220,
                "content": {
                    "title": "Shop & support",
                    "body": "Placeholder shop page for sponsorship, donations, and community support items. We can add real checkout later.",
                    "button_label": "Visit shop",
                    "button_url": "/shop",
                    "secondary_label": "Checkout",
                    "secondary_url": "/checkout",
                    "note": "This is not legal advice or medical advice. Always call 911 in an emergency.",
                },
            },
        ],
    }

    layout = PageLayout(page="home", layout_json=json.dumps(default))
    db.session.add(layout)
    db.session.commit()


def seed_sample_stories(app):
    """Create a few high-quality sample stories (approved) so the site doesn't look empty.
    These are clearly marked as examples and can be replaced later.
    """
    from .extensions import db
    from .models import Story

    sample = [
        {
            "title": "A fresh start with community support",
            "summary": "Stability, structure, and people who genuinely care made the difference.",
            "author_name": "Example story (replace later)",
            "image_url": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?auto=format&fit=crop&w=1600&q=80",
            "body": (
                "I came in feeling overwhelmed and unsure where to begin. The most helpful thing was having "
                "a consistent routine and a respectful environment. Little steps—showing up on time, planning meals, "
                "and practicing healthy boundaries—added up.\n\n"
                "What surprised me was how much encouragement mattered. When you feel seen, it's easier to keep going. "
                "This is an example story to demonstrate the layout; you can replace it with a real story anytime."
            ),
        },
        {
            "title": "Finding my footing after reentry",
            "summary": "With the right plan, reentry can become a bridge to long-term stability.",
            "author_name": "Example story (replace later)",
            "image_url": "https://images.unsplash.com/photo-1520975958225-4ed07d6c0f47?auto=format&fit=crop&w=1600&q=80",
            "body": (
                "Reentry can be isolating. Having a place that is substance-free, predictable, and supportive helped me "
                "focus on the next right choice. I worked on job applications, practiced interview skills, and learned "
                "how to organize my week.\n\n"
                "This is an example story to demonstrate the layout; you can replace it with a real story anytime."
            ),
        },
        {
            "title": "Peer support that actually helped",
            "summary": "Accountability doesn't have to feel harsh—sometimes it feels like hope.",
            "author_name": "Example story (replace later)",
            "image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1600&q=80",
            "body": (
                "I didn't need someone to lecture me—I needed people who understood the work. The peer support here "
                "was practical and respectful. We checked in, shared resources, and stayed focused.\n\n"
                "This is an example story to demonstrate the layout; you can replace it with a real story anytime."
            ),
        },
    ]

    with app.app_context():
        if Story.query.count() == 0:
            from .utils import slugify
            for item in sample:
                slug = slugify(item["title"])
                story = Story(
                    title=item["title"],
                    slug=slug,
                    summary=item["summary"],
                    body=item["body"],
                    image_url=item["image_url"],
                    author_name=item["author_name"],
                    status="approved",
                )
                db.session.add(story)
            db.session.commit()
