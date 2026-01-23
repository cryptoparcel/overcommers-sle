"""Small shared utilities.

We keep these helpers dependency-free so deploys stay stable.
"""

from __future__ import annotations

import re
from functools import wraps

from flask import abort
from flask_login import current_user


_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Convert text into a URL-safe slug.

    - lowercases
    - replaces non [a-z0-9] with single dashes
    - trims leading/trailing dashes
    """
    if not value:
        return ""
    v = value.strip().lower()
    v = _slug_re.sub("-", v)
    return v.strip("-")


def admin_required(fn):
    """Protect admin-only routes (no user-controlled elevation)."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            abort(403)
        return fn(*args, **kwargs)

    return wrapper

