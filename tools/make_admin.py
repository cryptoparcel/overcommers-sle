"""Make a user admin.
Usage (local):
  python tools/make_admin.py username_or_email
On Render (shell):
  python tools/make_admin.py username_or_email
"""

import sys
from wsgi import app
from app.extensions import db
from app.models import User


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/make_admin.py <username_or_email>")
        raise SystemExit(2)

    ident = sys.argv[1].strip().lower()

    with app.app_context():
        user = (
            User.query.filter(User.username.ilike(ident)).first()
            or User.query.filter(User.email.ilike(ident)).first()
        )
        if not user:
            print("User not found.")
            raise SystemExit(1)

        user.is_admin = True
        db.session.commit()
        print(f"✅ {user.username} is now admin.")


if __name__ == "__main__":
    main()
