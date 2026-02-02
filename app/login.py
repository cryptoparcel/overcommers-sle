from __future__ import annotations
from .extensions import login_manager
from .models import User

@login_manager.user_loader
def load_user(user_id: str):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None
