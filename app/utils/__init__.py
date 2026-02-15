
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
