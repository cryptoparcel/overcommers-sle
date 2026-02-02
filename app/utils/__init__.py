from __future__ import annotations

import re
from functools import wraps

from flask import abort
from flask_login import current_user


def slugify(value: str) -> str:
    """Create a URL-friendly slug."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value).strip("-")
    return value or "story"


def admin_required(fn):
    """Decorator: only allow authenticated admins."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return fn(*args, **kwargs)

    return wrapper
