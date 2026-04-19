
"""Utility helpers for OVERCOMERS.

Note:
- This is a package (app.utils.*). Keep shared helpers here.
- Do NOT add an app/utils.py file (it breaks package imports).
"""

from __future__ import annotations

import re
import unicodedata
from functools import wraps

from flask import abort
from flask_login import current_user


def admin_required(fn):
    """Require the current user to be logged in and marked as admin."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False):
            abort(401)
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def slugify(value: str) -> str:
    """Simple ASCII slug for URLs."""

    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    value = re.sub(r"[\s_-]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "item"


def log_activity(
    action: str,
    category: str = "general",
    details: str | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
    level: str = "info",
    user_id: int | None = None,
) -> None:
    """Write an immutable activity log entry.

    Safe to call from anywhere — silently fails if DB unavailable.
    """
    from flask import request as _req, has_request_context
    from flask_login import current_user as _cu

    try:
        from ..extensions import db
        from ..models import ActivityLog

        entry = ActivityLog(
            action=action[:80],
            category=category[:30],
            details=(details or "")[:4000] or None,
            resource_type=resource_type,
            resource_id=resource_id,
            level=level,
        )

        # User
        if user_id:
            entry.user_id = user_id
        elif hasattr(_cu, "id") and _cu.is_authenticated:
            entry.user_id = _cu.id

        # Request context
        if has_request_context():
            entry.ip_address = _req.headers.get("X-Forwarded-For", _req.remote_addr or "")[:45]
            entry.user_agent = (_req.user_agent.string or "")[:512]
            entry.path = (_req.path or "")[:500]
            entry.method = (_req.method or "")[:10]

        db.session.add(entry)
        db.session.commit()
    except Exception:
        # Never crash the app for logging failures
        try:
            from ..extensions import db
            db.session.rollback()
        except Exception:
            pass
