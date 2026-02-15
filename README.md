
# OVERCOMERS — Transformative Thinking & Restorative Community

Supportive housing management site built with Flask.

## Quick Start (Local)

```bash
pip install -r requirements.txt
python manage.py run
```

Visit http://localhost:5000

## How to Get Admin Access

### Option A: Environment variables (recommended for Render)

Set these in your Render service environment:
```
ADMIN_EMAIL=you@example.com
ADMIN_PASSWORD=your-secure-password
```
The app auto-creates the admin user on first request. After the account exists, you can remove `ADMIN_PASSWORD` from env vars.

### Option B: CLI command (local or Render Shell)

1. Register an account at `/auth/register`
2. Run in terminal (or Render Shell):
```bash
flask --app wsgi:app make-admin you@example.com
```
3. Visit `/admin` — you're in.

### Option C: manage.py (local)

```bash
python manage.py make-admin you@example.com
```

## Deploying to Render

1. Push code to GitHub
2. Create a Web Service on Render
3. Set environment variables:
   - `SECRET_KEY` — **required** (long random string, app won't start without it)
   - `DATABASE_URL` — auto-set if using Render Postgres
   - `SESSION_COOKIE_SECURE=1`
   - `ADMIN_EMAIL` — (optional) auto-creates admin on first deploy
   - `ADMIN_PASSWORD` — (optional) remove after first deploy

### Optional email notifications
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=you@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFY_EMAIL=info@overcomersrc.com
```

## Database Migrations

Render runs migrations automatically via `render.yaml`. Locally:
```bash
flask --app wsgi:app db upgrade
```

To generate a new migration after model changes:
```bash
flask --app wsgi:app db migrate -m "description"
```

## Project Structure

```
app/
  blueprints/    → Routes (public, auth, admin, errors)
  templates/     → Jinja2 HTML templates
  static/        → CSS, JS, images
  models.py      → Database models
  forms.py       → WTForms definitions
  config.py      → Configuration
  utils/         → Helpers (mailer, slugify, admin_required)
manage.py        → CLI commands
wsgi.py          → WSGI entry point
```

## Business Emails

| Email | Purpose | Where it appears |
|---|---|---|
| info@overcomersrc.com | General questions, tours | Footer, contact page |
| support@overcomersrc.com | Website issues | Contact directory |
| careers@overcomersrc.com | Jobs, volunteering | Careers page, contact directory |
| billing@overcomersrc.com | Payment questions | Shop, contact directory |
| legal@overcomersrc.com | Policies, formal requests | Privacy, terms, policies |
| mod@overcomersrc.com | Community conduct | Contact directory |
| sales@overcomersrc.com | Referral partnerships | Referrals page |
| marketing@overcomersrc.com | Outreach, events | Referrals page |
| admin@overcomersrc.com | Administrative escalation | Contact directory |
