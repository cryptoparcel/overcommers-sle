from __future__ import annotations

from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


# Rate limiting (defaults empty; apply limits per-route)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)
