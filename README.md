# Overcomers | SLE (Flask)

Production-ready Flask app with:
- Public marketing pages
- Apply + Contact forms (stored in DB)
- Optional email notifications via SMTP
- Auth (login/signup) + admin area (applications/messages/stories/users)
- Homepage Page Builder (drag/drop) + layout saved to DB
- Optional reCAPTCHA (enabled only if keys are set)
- Basic route tests (pytest)

## Local setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app wsgi:app run --debug
```

Then open http://127.0.0.1:5000

## First time database setup

For SQLite local dev:

```powershell
.\.venv\Scripts\activate
python manage.py bootstrap-db
```

## Create your first admin

1) Register a normal account in the UI.
2) Promote it to admin:

```powershell
.\.venv\Scripts\activate
python manage.py make-admin you@example.com
```

Log out and log back in, then visit `/admin/`.

## Render deployment

- Create a PostgreSQL database on Render.
- Set env vars on the Web Service:
  - `DATABASE_URL` = Render Postgres URL
  - `SECRET_KEY` = long random string

Optional:
- SMTP vars from `.env.example`
- `RECAPTCHA_SITE_KEY` + `RECAPTCHA_SECRET_KEY`

Start command:
`gunicorn --bind 0.0.0.0:$PORT wsgi:app`
