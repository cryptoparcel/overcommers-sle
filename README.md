# Overcomers — Transformative Thinking & Restorative Community

A premium, structured sober-living / supportive-housing website built with Flask.

## Features

- Public pages: Home, What We Do, Resources, Impact, Shop, Contact, Apply
- Openings: Published housing listings with pricing, amenities, house rules
- Stories: User-submitted stories with admin approval workflow
- Accounts: signup/login, account settings, logout
- Admin area (admins only):
  - Applications management (status updates, CSV export)
  - Contact messages inbox
  - Stories moderation (approve / reject / delete)
  - Users list
  - Page Builder (drag-and-drop homepage blocks)
  - Openings CRUD (create & publish "Upcoming Openings" listings)

## Local setup

1) Create a virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

2) Set environment variables:

```bash
export FLASK_APP="wsgi:app"
export SECRET_KEY="change-me"
export DATABASE_URL="sqlite:///app.db"
```

3) Create the database and seed starter content:

```bash
flask db upgrade
flask bootstrap-db
```

4) Run the app:

```bash
flask run
```

## Making yourself admin

There is **no** UI button to become admin (by design).

1) Create an account on the site (Signup)
2) In a terminal, run:

```bash
flask make-admin your@email.com

# Or using manage.py:
python manage.py make-admin your@email.com
```

Now refresh — you'll see the **Admin** link in the navbar.

## Openings (Upcoming Openings)

- Admin → Openings → "New opening"
- Set **Status = Published** to show it on `/openings`
- Recommended: leave **Hide pricing publicly** checked (pricing is shared after application)

## Deploying on Render

The included `render.yaml` handles deployment. Key steps:

1. Set `DATABASE_URL` to your Render Postgres internal URL
2. Set `SECRET_KEY` to a strong random string (e.g. `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
3. Set `SESSION_COOKIE_SECURE=1`
4. The start command runs `flask db upgrade` automatically before starting Gunicorn
5. After first deploy, open the Render Shell and run:

```bash
flask bootstrap-db
flask make-admin you@example.com
```

## Optional configuration

| Variable | Purpose |
|---|---|
| `SMTP_HOST` | SMTP server for email notifications |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USERNAME` | SMTP login |
| `SMTP_PASSWORD` | SMTP password |
| `SMTP_FROM` | From address for emails |
| `NOTIFY_EMAIL` | Where to send admin notifications (default: info@overcomersrc.com) |
| `RECAPTCHA_SITE_KEY` | Google reCAPTCHA v3 site key |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA v3 secret key |
