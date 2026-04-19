
from __future__ import annotations

import json
from datetime import datetime, timezone

from .extensions import db
from .models import PageLayout, Story
from .utils import slugify


def _default_home_layout_json() -> str:
    """Starter layout for the homepage Page Builder."""
    payload = {
        "version": 1,
        "canvas": {"minHeight": 560},
        "blocks": [
            {
                "id": "classes",
                "type": "card",
                "x": 0,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Life‑skills classes",
                    "body": "Weekly workshops: routines, budgeting, job search, and basic life skills.",
                    "buttons": [{"label": "What we do", "href": "/what-we-do"}],
                },
            },
            {
                "id": "openings",
                "type": "card",
                "x": 51,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Upcoming openings",
                    "body": "View current openings near Grover Beach and apply in a few minutes.",
                    "buttons": [{"label": "View openings", "href": "/openings"}, {"label": "Apply", "href": "/apply"}],
                    "note": "Pricing is shared after a quick application so we can confirm fit and next steps.",
                },
            },
            {
                "id": "lumpia",
                "type": "card",
                "x": 0,
                "y": 240,
                "w": 100,
                "h": 220,
                "content": {
                    "title": "Lumpia Bros Cafe jobs",
                    "body": "Employment pathway and training opportunities in Grover Beach.",
                    "buttons": [{"label": "Careers", "href": "/careers"}, {"label": "Contact", "href": "/contact"}],
                },
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def seed_content() -> None:
    """Seed minimal default content for a fresh database."""

    # Page builder starter layout
    layout = PageLayout.query.filter_by(page="home").first()
    if not layout:
        db.session.add(PageLayout(page="home", layout_json=_default_home_layout_json()))
        db.session.commit()

    # Sample stories (optional, safe placeholders)
    if Story.query.count() == 0:
        samples = [
            {
                "title": "Finding stability again",
                "summary": "A simple routine and a supportive home can make life feel possible again.",
                "body": "This is a placeholder story. Replace with consented stories only.",
                "image_url": "",
                "author_name": "Anonymous",
                "status": "approved",
            },
            {
                "title": "Step‑by‑step reentry",
                "summary": "Small steps: phone, email, job search — one day at a time.",
                "body": "This is a placeholder story. Replace with consented stories only.",
                "image_url": "",
                "author_name": "Anonymous",
                "status": "approved",
            },
        ]
        for s in samples:
            db.session.add(
                Story(
                    title=s["title"],
                    slug=slugify(s["title"]),
                    summary=s["summary"],
                    body=s["body"],
                    image_url=s["image_url"] or None,
                    author_name=s["author_name"],
                    status=s["status"],
                    created_at=datetime.now(timezone.utc),
                )
            )
        db.session.commit()
