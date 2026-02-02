from __future__ import annotations

import json
from datetime import datetime
from .extensions import db
from .models import PageLayout, Story
from .utils import slugify

def _default_home_layout_json() -> str:
    payload = {
        "version": 1,
        "canvas": {"minHeight": 560},
        "blocks": [
            {
                "id": "resources",
                "type": "card",
                "x": 0,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Resources",
                    "body": "Simple, kid‑friendly and family‑friendly links to get help, learn next steps, and find local support.",
                    "buttons": [{"label": "Go to resources", "href": "/resources"}],
                },
            },
            {
                "id": "shop",
                "type": "card",
                "x": 51,
                "y": 0,
                "w": 49,
                "h": 220,
                "content": {
                    "title": "Shop & support",
                    "body": "Support items, sponsorship, and donations. We can connect real checkout when you're ready.",
                    "buttons": [
                        {"label": "Visit shop", "href": "/shop"},
                        {"label": "Checkout", "href": "/checkout"},
                    ],
                    "note": "This is not legal advice or medical advice. Always call 911 in an emergency.",
                },
            },
        ],
    }
    return json.dumps(payload, ensure_ascii=False)

def seed_defaults() -> None:
    # Default homepage layout
    if PageLayout.query.filter_by(page="home").first() is None:
        db.session.add(PageLayout(page="home", layout_json=_default_home_layout_json()))
        db.session.commit()

    # Sample stories so the site isn't empty
    if Story.query.count() == 0:
        samples = [
            {
                "title": "Rebuilding routines, one morning at a time",
                "summary": "A short example story about structure, accountability, and small wins.",
                "body": "This is a sample story. Replace with real stories whenever you're ready.\n\nProgress can be simple: wake up, make the bed, show up for the day, and keep going.",
                "image_url": "https://images.unsplash.com/photo-1526256262350-7da7584cf5eb?auto=format&fit=crop&w=1800&q=80",
                "author_name": "Overcomers community",
                "status": "approved",
            },
            {
                "title": "From chaos to consistency",
                "summary": "An example of how peer support + clear expectations can help.",
                "body": "This is a sample story. The goal is to show a calm, hopeful tone and remind visitors that change is possible.",
                "image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1800&q=80",
                "author_name": "Overcomers community",
                "status": "approved",
            },
        ]
        for s in samples:
            db.session.add(Story(
                title=s["title"],
                slug=slugify(s["title"]),
                summary=s["summary"],
                body=s["body"],
                image_url=s["image_url"],
                author_name=s["author_name"],
                status=s["status"],
                created_at=datetime.utcnow(),
            ))
        db.session.commit()
